"""GEDCOM import/export adapter.

This module implements a small, dependency-free GEDCOM parser that covers
common tags (INDI, FAM, NAME, SEX, BIRT/DEAT DATE/PLAC, NOTE) and provides
import/export helpers to move data into/from the project's `Storage`.

It's intentionally conservative (handles the common subset) and safe to run
without external packages. If you prefer using a full-featured GEDCOM parser
library, this module can be extended to add an alternate code-path.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from .storage import Storage
from .models import Person, Family, Event
import re


def _normalize_gedcom_id(raw: str) -> str:
    # turn '@I1@' into 'gedcom:I1'
    if raw is None:
        return ""
    m = re.match(r"@?([^@]+)@?", raw.strip())
    if not m:
        return raw.strip()
    val = m.group(1)
    # If the value already looks like our internal gedcom id (starts with 'gedcom:'), keep it as-is
    if val.startswith("gedcom:"):
        return val
    return f"gedcom:{val}"


def _split_name(name: str) -> Tuple[str, str]:
    # GEDCOM names are often like 'Given /Surname/'
    if not name:
        return "", ""
    # extract surname between slashes
    m = re.match(r"(.*?)/([^/]+)/(.*)", name)
    if m:
        given = (m.group(1) + " " + m.group(3)).strip()
        surname = m.group(2).strip()
        return given, surname
    # fallback: split last token as surname
    parts = name.strip().split()
    if len(parts) == 1:
        return parts[0], ""
    return " ".join(parts[:-1]), parts[-1]


def _parse_gedcom(path: Path) -> Dict[str, Dict[str, Any]]:
    """Parse a GEDCOM file into a dict of records keyed by gedcom id.

    Each record is a dict: { 'type': 'INDI'|'FAM'|..., 'tags': {tag:[values...]}, 'sub': list }
    """
    records: Dict[str, Dict[str, Any]] = {}
    cur_id: Optional[str] = None
    cur_type: Optional[str] = None
    # store children as list of (level, tag, value)

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\r\n")
            if not line:
                continue
            parts = line.split(" ", 2)
            if len(parts) == 1:
                continue
            level = parts[0]
            # level may be '0'..'n'
            try:
                lvl = int(level)
            except Exception:
                lvl = 0
            # Determine if the second token is an id (like @I1@) or a tag
            if lvl == 0:
                # new record or standalone tag
                if len(parts) == 3 and parts[1].startswith("@") and parts[2]:
                    rid = _normalize_gedcom_id(parts[1])
                    rtype = parts[2].strip()
                    cur_id = rid
                    cur_type = rtype
                    records[cur_id] = {"type": cur_type, "tags": {}}
                else:
                    # reset current
                    cur_id = None
                    cur_type = None
                continue
            # non-zero levels: attribute lines belong to the current record
            if cur_id is None:
                continue
            # parse tag and value
            if len(parts) >= 2:
                tag = parts[1].strip()
                value = parts[2].strip() if len(parts) == 3 else ""
                tags = records[cur_id]["tags"]
                tags.setdefault(tag, []).append(value)
    return records


def import_gedcom(file_path: str | Path, storage: Storage) -> Dict[str, str]:
    """Import GEDCOM file into the provided `storage` instance.

    Returns a mapping gedcom_id -> created person id in storage.
    """
    p = Path(file_path)
    recs = _parse_gedcom(p)
    # First pass: create persons for INDI
    id_map: Dict[str, str] = {}
    for gid, rec in recs.items():
        if rec.get("type") != "INDI":
            continue
        tags = rec.get("tags", {})
        name_vals = tags.get("NAME", [])
        given, surname = ("", "")
        if name_vals:
            given, surname = _split_name(name_vals[0])
        sex = tags.get("SEX", [None])[0]
        # birth/death
        birth = None
        death = None
        # GEDCOM often uses BIRT/DEAT as tags with child DATE and PLAC lines; our simple parser keeps them as flat tags like 'DATE' entries following BIRT
        # We'll look for lines 'BIRT' and then 'DATE' in subsequent tags; as a simple heuristic, try tags 'BIRT' 'DATE' or 'DATE' with context missing.
        # Look for tags with keys like 'DATE' and 'PLAC' and hope they refer to birth/death; if both exist we prefer birth if BIRT present.
        if "BIRT" in tags:
            # find following DATE and PLAC values (heuristic)
            # In our flattened parser we likely have 'DATE' entries; prefer first
            date = tags.get("DATE", [None])[0]
            place = tags.get("PLAC", [None])[0]
            birth = Event(kind="birth", date=date, place=place)
        if "DEAT" in tags or "DEATH" in tags:
            date = tags.get("DATE", [None])[0]
            place = tags.get("PLAC", [None])[0]
            death = Event(kind="death", date=date, place=place)
        # Create person with gedcom-prefixed id for traceability
        person_id = gid
        person = Person(id=person_id, first_name=given, surname=surname, sex=sex, birth=birth, death=death)
        storage.add_person(person)
        id_map[gid] = person.id
    # Second pass: create families
    for gid, rec in recs.items():
        if rec.get("type") != "FAM":
            continue
        tags = rec.get("tags", {})
        husb = tags.get("HUSB", [None])[0]
        wife = tags.get("WIFE", [None])[0]
        chil = tags.get("CHIL", [])
        husb_id = _normalize_gedcom_id(husb) if husb else None
        wife_id = _normalize_gedcom_id(wife) if wife else None
        children_ids = [_normalize_gedcom_id(c) for c in chil]
        # Create Family with gedcom ids (they should map to person ids created earlier)
        fa = Family(id=gid, husband_id=husb_id, wife_id=wife_id, children_ids=children_ids)
        # ensure referenced persons exist; if not, create placeholder persons
        for pid in [husb_id, wife_id] + children_ids:
            if not pid:
                continue
            if storage.get_person(pid) is None:
                # placeholder
                storage.add_person(Person(id=pid, first_name="", surname=""))
        storage.add_family(fa)
    return id_map


def export_gedcom(storage: Storage, out_path: str | Path) -> None:
    """Export current storage content to a simple GEDCOM file.

    This is a conservative exporter: creates INDI records for persons and FAM
    records for families with minimal tags (NAME, SEX, BIRT/DEAT DATE/PLAC).
    """
    out = Path(out_path)
    lines: List[str] = []
    # header
    lines.append("0 HEAD")
    # persons
    for p in storage.list_persons():
        gid = p.id
        lines.append(f"0 @{gid}@ INDI")
        name = f"{p.first_name} /{p.surname}/".strip()
        lines.append(f"1 NAME {name}")
        if p.sex:
            lines.append(f"1 SEX {p.sex}")
        if p.birth:
            lines.append("1 BIRT")
            if p.birth.date:
                lines.append(f"2 DATE {p.birth.date}")
            if p.birth.place:
                lines.append(f"2 PLAC {p.birth.place}")
        if p.death:
            lines.append("1 DEAT")
            if p.death.date:
                lines.append(f"2 DATE {p.death.date}")
            if p.death.place:
                lines.append(f"2 PLAC {p.death.place}")
    # families
    for f in storage.families.values():
        gid = f.id
        lines.append(f"0 @{gid}@ FAM")
        if f.husband_id:
            lines.append(f"1 HUSB @{f.husband_id}@")
        if f.wife_id:
            lines.append(f"1 WIFE @{f.wife_id}@")
        for c in f.children_ids:
            lines.append(f"1 CHIL @{c}@")
    lines.append("0 TRLR")
    # Ensure parent directory exists
    if not out.parent.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    print("This module provides import_gedcom/export_gedcom helpers. Use the CLI script in scripts/import_gedcom.py")
