"""Storage layer backed by SQLite (keeps same public API as the previous
file-backed JSON implementation). This implementation stores the persons,
families and notes metadata as JSON blobs in an SQLite database located at
``<root>/storage.db``. The `notes_d/` convention (file-backed note bodies)
is preserved: committing a note writes a file under `notes_d/` and the
metadata is stored in the DB as before.

The class keeps `self.persons`, `self.families`, `self.notes` dicts in memory
so the rest of the codebase (and tests) can access them directly as before.
"""
from __future__ import annotations
from typing import Dict, Optional, List, Set, Iterable, Any
from .fs import atomic_write_text, read_text, normalize_note_id
from pathlib import Path
import threading
from .models import Person, Family, Note, CDate, Place, PersEvent
import sqlite3
import json
import contextvars


def _dict_to_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)


def _json_to_dict(s: str) -> Any:
    return json.loads(s) if s else None


class Storage:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        # simple lock to guard DB writes from multiple threads
        self._lock = threading.RLock()
        # sqlite DB path
        self._db_file = self.root / "storage.db"
        # SQLite connection (opened lazily)
        self._conn = None
        self._connect()
        self._ensure_tables()
        self._load()

    def _connect(self) -> None:
        if self._conn is None:
            # Allow using the connection from different threads (uvicorn/fastapi may run handlers
            # in worker threads). We'll protect concurrent access with a threading lock.
            self._conn = sqlite3.connect(str(self._db_file), check_same_thread=False)
            # Use row factory for convenience
            self._conn.row_factory = sqlite3.Row

    def _ensure_tables(self) -> None:
        cur = self._conn.cursor()
        # New schema: use JSON columns for structured fields (pevents, places)
        # and normalized columns for commonly queried fields.
        # Create missing tables if they do not already exist — do NOT drop existing tables
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS persons(
                id TEXT PRIMARY KEY,
                first_name TEXT,
                surname TEXT,
                sex TEXT,
                birth_date TEXT,
                birth_place_json TEXT,
                birth_note TEXT,
                death_date TEXT,
                death_place_json TEXT,
                death_note TEXT,
                pevents_json TEXT,
                notes_json TEXT
            );
            CREATE TABLE IF NOT EXISTS families(
                id TEXT PRIMARY KEY,
                husband_id TEXT,
                wife_id TEXT,
                fevents_json TEXT
            );
            CREATE TABLE IF NOT EXISTS family_children(
                family_id TEXT,
                child_id TEXT
            );
            CREATE TABLE IF NOT EXISTS notes(
                id TEXT PRIMARY KEY,
                title TEXT,
                text TEXT
            );
            """
        )
        self._conn.commit()

    def _load(self) -> None:
        # In-memory caches (same public API as previous implementation)
        self.persons: Dict[str, Person] = {}
        self.families: Dict[str, Family] = {}
        self.notes: Dict[str, Note] = {}

        cur = self._conn.cursor()
        # Load persons from normalized + JSON columns
        cur.execute(
            "SELECT id, first_name, surname, sex, birth_date, birth_place_json, birth_note, death_date, death_place_json, death_note, pevents_json, notes_json FROM persons"
        )
        for row in cur.fetchall():
            try:
                notes_list = []
                if row["notes_json"]:
                    try:
                        notes_list = json.loads(row["notes_json"])
                    except Exception:
                        notes_list = []
                # parse birth/death places as structured Place if present
                birth_place = None
                if row["birth_place_json"]:
                    try:
                        birth_place = Place.from_dict(json.loads(row["birth_place_json"]))
                    except Exception:
                        birth_place = None
                death_place = None
                if row["death_place_json"]:
                    try:
                        death_place = Place.from_dict(json.loads(row["death_place_json"]))
                    except Exception:
                        death_place = None
                # parse pevents
                pevents = []
                if row["pevents_json"]:
                    try:
                        evs = json.loads(row["pevents_json"]) or []
                        pevents = [PersEvent.from_dict(e) for e in evs]
                    except Exception:
                        pevents = []
                p = Person(
                    id=row["id"],
                    first_name=row["first_name"] or "",
                    surname=row["surname"] or "",
                    sex=row["sex"],
                    birth_date=CDate.from_string(row["birth_date"]) if row["birth_date"] else None,
                    birth_place=birth_place,
                    birth_note=row["birth_note"],
                    death_date=CDate.from_string(row["death_date"]) if row["death_date"] else None,
                    death_place=death_place,
                    death_note=row["death_note"],
                    pevents=pevents,
                    notes=notes_list,
                )
                self.persons[p.id] = p
            except Exception:
                continue

        # Load families and their children
        cur.execute("SELECT id, husband_id, wife_id, fevents_json FROM families")
        for row in cur.fetchall():
            try:
                fid = row["id"]
                # collect children
                cur2 = self._conn.cursor()
                cur2.execute("SELECT child_id FROM family_children WHERE family_id = ?", (fid,))
                children = [r["child_id"] for r in cur2.fetchall()]
                fevents_list = []
                if row["fevents_json"]:
                    try:
                        fevents_list = json.loads(row["fevents_json"]) or []
                    except Exception:
                        fevents_list = []
                d = {
                    "id": fid,
                    "husband_id": row["husband_id"],
                    "wife_id": row["wife_id"],
                    "children_ids": children,
                    "fevents": fevents_list,
                }
                fa = Family.from_dict(d)
                self.families[fa.id] = fa
            except Exception:
                continue

        # Load notes
        cur.execute("SELECT id, title, text FROM notes")
        for row in cur.fetchall():
            try:
                d = {"id": row["id"], "title": row["title"] or "", "text": row["text"] or ""}
                n = Note.from_dict(d)
                self.notes[n.id] = n
            except Exception:
                continue
        notes_d = self.root / "notes_d"
        if notes_d.exists():
            for p in notes_d.rglob("*.txt"):
                try:
                    rel = p.relative_to(notes_d).as_posix()
                except Exception:
                    rel = p.name
                nid = rel[:-4] if rel.endswith(".txt") else rel
                try:
                    txt = read_text(p, default="") or ""
                except Exception:
                    txt = ""
                title = p.stem
                # File-backed notes override DB entries
                self.notes[nid] = Note(id=nid, title=title, text=txt)
        # Build initial family index for fast lookups
        self._rebuild_index()

    def _save(self) -> None:
        # Persist current in-memory dictionaries into the SQLite DB
        # Acquire lock to avoid concurrent sqlite access from different threads
        with self._lock:
            cur = self._conn.cursor()
        # Replace persons (normalized + JSON columns)
        cur.execute("DELETE FROM persons")
        for p in self.persons.values():
            birth_date = p.birth_date.to_iso() if p.birth_date else None
            birth_place_json = json.dumps(p.birth_place.to_dict(), ensure_ascii=False) if p.birth_place else None
            birth_note = p.birth_note if getattr(p, "birth_note", None) else None
            death_date = p.death_date.to_iso() if p.death_date else None
            death_place_json = json.dumps(p.death_place.to_dict(), ensure_ascii=False) if p.death_place else None
            death_note = p.death_note if getattr(p, "death_note", None) else None
            pevents_json = json.dumps([e.to_dict() for e in p.pevents], ensure_ascii=False) if p.pevents else None
            notes_json = json.dumps(p.notes, ensure_ascii=False) if p.notes else None
            cur.execute(
                "INSERT INTO persons(id, first_name, surname, sex, birth_date, birth_place_json, birth_note, death_date, death_place_json, death_note, pevents_json, notes_json) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    p.id,
                    p.first_name,
                    p.surname,
                    p.sex,
                    birth_date,
                    birth_place_json,
                    birth_note,
                    death_date,
                    death_place_json,
                    death_note,
                    pevents_json,
                    notes_json,
                ),
            )

        # Replace families and family_children
        cur.execute("DELETE FROM family_children")
        cur.execute("DELETE FROM families")
        for fa in self.families.values():
            fevents_json = json.dumps([e.to_dict() for e in getattr(fa, "fevents", [])], ensure_ascii=False) if getattr(fa, "fevents", None) else None
            cur.execute(
                "INSERT INTO families(id, husband_id, wife_id, fevents_json) VALUES(?, ?, ?, ?)",
                (fa.id, fa.husband_id, fa.wife_id, fevents_json),
            )
            # insert children rows
            for cid in fa.children_ids:
                cur.execute(
                    "INSERT INTO family_children(family_id, child_id) VALUES(?, ?)",
                    (fa.id, cid),
                )

        # Replace notes metadata
        cur.execute("DELETE FROM notes")
        for n in self.notes.values():
            cur.execute("INSERT INTO notes(id, title, text) VALUES(?, ?, ?)", (n.id, n.title, n.text))

        self._conn.commit()
        # Ensure index stays consistent with current families
        self._rebuild_index()

    # Person operations
    def add_person(self, person: Person) -> None:
        self.persons[person.id] = person
        self._save()

    def get_person(self, pid: str) -> Optional[Person]:
        return self.persons.get(pid)

    def list_persons(self) -> List[Person]:
        return list(self.persons.values())

    # Family operations
    def add_family(self, family: Family) -> None:
        self.families[family.id] = family
        # incremental index update
        try:
            self._index_family(family)
        except Exception:
            # ensure index exists
            self._rebuild_index()
            self._index_family(family)
        self._save()

    def get_family(self, fid: str) -> Optional[Family]:
        return self.families.get(fid)

    # Notes
    def add_note(self, note: Note) -> None:
        self.notes[note.id] = note
        self._save()

    def get_note(self, nid: str) -> Optional[Note]:
        # If a file exists in notes_d, prefer its content
        fpath = self.root / "notes_d" / (nid + ".txt")
        if fpath.exists():
            try:
                txt = read_text(fpath, default="") or ""
            except Exception:
                txt = ""
            title = fpath.stem
            return Note(id=nid, title=title, text=txt)
        return self.notes.get(nid)

    # --- Family indexing: person_id -> set of family ids ---
    def _rebuild_index(self) -> None:
        # Map person id -> set of family ids where they appear
        self.families_by_person: Dict[str, Set[str]] = {}
        for fid, fam in self.families.items():
            self._index_family(fam)

    def _index_family(self, fam: Family) -> None:
        fid = fam.id
        if fam.husband_id:
            self.families_by_person.setdefault(fam.husband_id, set()).add(fid)
        if fam.wife_id:
            self.families_by_person.setdefault(fam.wife_id, set()).add(fid)
        for cid in fam.children_ids:
            self.families_by_person.setdefault(cid, set()).add(fid)

    def _unindex_family(self, fam: Family) -> None:
        fid = fam.id
        if fam.husband_id and fam.husband_id in self.families_by_person:
            self.families_by_person.get(fam.husband_id, set()).discard(fid)
        if fam.wife_id and fam.wife_id in self.families_by_person:
            self.families_by_person.get(fam.wife_id, set()).discard(fid)
        for cid in fam.children_ids:
            if cid in self.families_by_person:
                self.families_by_person.get(cid, set()).discard(fid)

    def families_of_person(self, pid: str) -> Iterable[Family]:
        fids = self.families_by_person.get(pid, set())
        for fid in fids:
            fam = self.families.get(fid)
            if fam:
                yield fam

    # Notes helpers
    def list_notes(self) -> Iterable[Note]:
        """List all notes from notes.json and notes_d (file-backed)."""
        # Ensure notes_d files are represented
        seen = set()
        notes_d = self.root / "notes_d"
        if notes_d.exists():
            for p in notes_d.rglob("*.txt"):
                try:
                    rel = p.relative_to(notes_d).as_posix()
                except Exception:
                    rel = p.name
                nid = rel[:-4] if rel.endswith(".txt") else rel
                try:
                    txt = read_text(p, default="") or ""
                except Exception:
                    txt = ""
                title = p.stem
                seen.add(nid)
                yield Note(id=nid, title=title, text=txt)
        # Now yield notes from notes.json that aren't overridden by files
        for nid, n in self.notes.items():
            if nid in seen:
                continue
            yield n

    def note_file_path(self, nid: str) -> Path:
        """Return the filesystem path for a notes_d note id."""
        notes_d = self.root / "notes_d"
        # normalize note id to avoid path traversal
        safe = normalize_note_id(nid)
        return notes_d / (safe + ".txt")

    def commit_note(self, nid: str, title: str, text: str) -> None:
        """Write note content to notes_d/<nid>.txt and update metadata."""
        path = self.note_file_path(nid)
        # atomic write for safety
        atomic_write_text(path, text)
        # Update notes metadata cache
        self.notes[nid] = Note(id=nid, title=title or path.stem, text=text)
        self._save()

    def delete_note(self, nid: str) -> bool:
        # Remove file if exists
        path = self.note_file_path(nid)
        removed = False
        if path.exists():
            try:
                path.unlink()
                removed = True
            except Exception:
                pass
        # Remove from notes.json cache
        if nid in self.notes:
            del self.notes[nid]
            self._save()
            removed = True
        return removed

    # Update / Delete operations
    def update_person(self, person: Person) -> None:
        if person.id in self.persons:
            self.persons[person.id] = person
            self._save()
        else:
            raise KeyError(f"Person {person.id} not found")

    def delete_person(self, pid: str) -> bool:
        if pid in self.persons:
            # Remove references in families
            for fid, fam in list(self.families.items()):
                changed = False
                if fam.husband_id == pid:
                    fam.husband_id = None
                    changed = True
                if fam.wife_id == pid:
                    fam.wife_id = None
                    changed = True
                if pid in fam.children_ids:
                    fam.children_ids = [c for c in fam.children_ids if c != pid]
                    changed = True
                if changed:
                    self.families[fid] = fam
            # rebuild index after modifications
            self._rebuild_index()
            del self.persons[pid]
            self._save()
            return True
        return False

    def update_family(self, family: Family) -> None:
        if family.id in self.families:
            old = self.families[family.id]
            # unindex old representation
            try:
                self._unindex_family(old)
            except Exception:
                pass
            self.families[family.id] = family
            # index new
            try:
                self._index_family(family)
            except Exception:
                self._rebuild_index()
                self._index_family(family)
            self._save()
        else:
            raise KeyError(f"Family {family.id} not found")

    def delete_family(self, fid: str) -> bool:
        if fid in self.families:
            fam = self.families[fid]
            try:
                self._unindex_family(fam)
            except Exception:
                # fallback to full rebuild later
                pass
            del self.families[fid]
            # ensure index correctness
            self._rebuild_index()
            self._save()
            return True
        return False


# --- Request-scoped storage support -------------------------------------------------
# A ContextVar holds the Storage instance bound to the current request (if any).
CURRENT_STORAGE: contextvars.ContextVar[Optional["Storage"]] = contextvars.ContextVar(
    "gw_current_storage", default=None
)


def bind_current_storage(s: Optional["Storage"]):
    """Bind a Storage instance to the current context and return the token.

    The caller should reset the ContextVar with the returned token when the
    request handling finishes (or call CURRENT_STORAGE.set(None)).
    """
    return CURRENT_STORAGE.set(s)


def get_current_storage() -> Optional["Storage"]:
    return CURRENT_STORAGE.get()


class StorageManager:
    """Manage multiple Storage instances (one per database / base name).

    Conventions:
    - `root` is a directory containing subdirectories for each base.
    - A base is an immediate subdirectory of `root` that contains a file
      named `storage.db` (the sqlite DB used by Storage). When a new base is
      requested and its directory does not exist, it will be created and a
      fresh Storage instance will be initialized there.
    """

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._cache: Dict[str, Storage] = {}

    def list_bases(self) -> List[str]:
        """Return sorted list of available base names (subdirectories that look
        like bases)."""
        names: List[str] = []
        try:
            for p in sorted(self.root.iterdir()):
                if p.is_dir() and (p / "storage.db").exists():
                    names.append(p.name)
        except Exception:
            # If iteration fails, return empty list
            return []
        return names

    def get_storage(self, name: str) -> Storage:
        """Return a Storage instance for base `name`. Creates one lazily and
        caches it for reuse within this process."""
        with self._lock:
            if name in self._cache:
                return self._cache[name]
            root = self.root / name
            root.mkdir(parents=True, exist_ok=True)
            s = Storage(root)
            self._cache[name] = s
            return s


class _RequestStorageProxy:
    """A transparent proxy that forwards attribute access to the Storage
    instance bound to the current request (via CURRENT_STORAGE). If no
    Storage is bound, it lazily creates a default Storage rooted at the
    provided `default_root` path.
    """

    def __init__(self, default_root: Path):
        self._default_root = Path(default_root)
        self._default: Optional[Storage] = None

    def _ensure_default(self):
        if self._default is None:
            self._default = Storage(self._default_root)

    def __getattr__(self, name: str):
        s = get_current_storage()
        if s is not None:
            return getattr(s, name)
        # fallback to a process-global default storage (for tooling/tests)
        self._ensure_default()
        return getattr(self._default, name)


# Export a process-global proxy named `storage` so existing code that does
# `from ..storage import storage` keeps working. By default it uses the
# `data/` directory in the current working directory.
storage = _RequestStorageProxy(Path("data"))

