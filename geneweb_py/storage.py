"""Simple file-based storage layer (JSON) as a placeholder for .gw handling."""
from __future__ import annotations
from typing import Dict, Optional, List, Set, Iterable
from .fs import json_load, json_save, atomic_write_text, read_text, normalize_note_id
from pathlib import Path
from .models import Person, Family, Note


class Storage:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._persons_file = self.root / "persons.json"
        self._families_file = self.root / "families.json"
        self._notes_file = self.root / "notes.json"
        self._load()

    def _load(self) -> None:
        self.persons: Dict[str, Person] = {}
        self.families: Dict[str, Family] = {}
        self.notes: Dict[str, Note] = {}
        arr = json_load(self._persons_file, default=[])
        for d in arr or []:
            p = Person.from_dict(d)
            self.persons[p.id] = p
        arr = json_load(self._families_file, default=[])
        for d in arr or []:
            fa = Family.from_dict(d)
            self.families[fa.id] = fa
        arr = json_load(self._notes_file, default=[])
        for d in arr or []:
            n = Note.from_dict(d)
            self.notes[n.id] = n
        # Also load notes from notes_d directory (file-backed notes). Files override notes.json entries.
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
                self.notes[nid] = Note(id=nid, title=title, text=txt)
        # Build initial family index for fast lookups
        self._rebuild_index()

    def _save(self) -> None:
        json_save(self._persons_file, [p.to_dict() for p in self.persons.values()])
        json_save(self._families_file, [fa.to_dict() for fa in self.families.values()])
        # Persist notes metadata to notes.json (disk-backed note content remains in notes_d files)
        json_save(self._notes_file, [n.to_dict() for n in self.notes.values()])
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
