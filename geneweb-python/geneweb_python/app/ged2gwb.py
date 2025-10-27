"""ged2gwb: Import GEDCOM into Database.

Minimal GEDCOM parser/importer:
- Parses INDI (individuals) and FAM (families)
- Links spouses (HUSB/WIFE), children (CHIL), and child-parent (FAMS/FAMC)
- Stores in core.database.Database
"""
from __future__ import annotations

import re
from typing import Dict, Optional, List, Tuple

try:
    from core.database import Database
    from core.models import CDate, Person, Family, Ascend
except Exception as exc:  # pragma: no cover
    raise RuntimeError(
        "core modules not found. Ensure you run from the repo root."
    ) from exc


def _parse_date(date_str: str) -> Optional[CDate]:
    """Parse a GEDCOM DATE string into a CDate.

    Supports:
      DD MON YYYY
      MON YYYY
      YYYY
    """
    date_str = date_str.strip()
    months = {
        "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
        "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
    }
    # Try: DD MON YYYY
    m = re.match(r"(\d{1,2})\s+(\w+)\s+(\d+)", date_str)
    if m:
        day, mon, year = m.groups()
        return CDate(day=int(day), month=months.get(mon.upper()), year=int(year))
    # Try: MON YYYY
    m = re.match(r"(\w+)\s+(\d+)", date_str)
    if m:
        mon, year = m.groups()
        return CDate(month=months.get(mon.upper()), year=int(year))
    # Try: YYYY
    m = re.match(r"(\d+)", date_str)
    if m:
        return CDate(year=int(m.group(1)))
    return None


def _parse_gedcom_lines(file_path: str) -> List[Tuple[int, str, str]]:
    """Parse GEDCOM into (level, tag, value) triples."""
    lines = []
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\r\n")
            parts = line.split(None, 2)
            if not parts:
                continue
            level = int(parts[0])
            tag = parts[1] if len(parts) > 1 else ""
            value = parts[2] if len(parts) > 2 else ""
            lines.append((level, tag, value))
    return lines


def import_gedcom(file_path: str, db: Database) -> None:
    """Import a GEDCOM file into the given Database.

    This is a minimal implementation that supports:
      - INDI: NAME, SEX, BIRT (DATE/PLAC), DEAT (DATE/PLAC), FAMS, FAMC
      - FAM: MARR (DATE/PLAC), HUSB, WIFE, CHIL
    """
    lines = _parse_gedcom_lines(file_path)

    # First pass: build INDI and FAM records
    indi_map: Dict[str, int] = {}  # xref -> person_id
    fam_map: Dict[str, int] = {}   # xref -> family_id

    i = 0
    while i < len(lines):
        level, tag, value = lines[i]
        if level == 0 and tag.startswith("@") and tag.endswith("@"):
            xref = tag
            record_type = value
            i += 1
            if record_type == "INDI":
                person_data, next_i = _parse_indi_record(lines, i)
                pid = db.add_person(**person_data)
                indi_map[xref] = pid
                i = next_i
            elif record_type == "FAM":
                family_data, next_i = _parse_fam_record(lines, i)
                fid = db.add_family(**family_data)
                fam_map[xref] = fid
                i = next_i
            else:
                i += 1
        else:
            i += 1

    # Second pass: link HUSB/WIFE, CHIL, FAMS, FAMC
    i = 0
    while i < len(lines):
        level, tag, value = lines[i]
        if level == 0 and tag.startswith("@") and tag.endswith("@"):
            xref = tag
            record_type = value
            i += 1
            if record_type == "INDI":
                _link_indi_record(db, indi_map, fam_map, xref, lines, i)
                i = _skip_record(lines, i)
            elif record_type == "FAM":
                _link_fam_record(db, indi_map, fam_map, xref, lines, i)
                i = _skip_record(lines, i)
            else:
                i += 1
        else:
            i += 1

    db.save()


def _parse_indi_record(lines: List[Tuple[int, str, str]], start: int) -> Tuple[dict, int]:
    """Parse INDI record for basic person data. Returns (data, next_index)."""
    data = {
        "first_name": "",
        "surname": "",
        "sex": "",
        "birth": None,
        "birth_place": "",
        "death": None,
        "death_place": "",
    }
    i = start
    while i < len(lines):
        level, tag, value = lines[i]
        if level == 0:
            break
        if level == 1:
            if tag == "NAME":
                # Parse NAME: "First /Last/"
                m = re.match(r"([^/]*)/([^/]*)/", value)
                if m:
                    data["first_name"] = m.group(1).strip()
                    data["surname"] = m.group(2).strip()
            elif tag == "SEX":
                data["sex"] = value.strip()
            elif tag == "BIRT":
                i += 1
                while i < len(lines) and lines[i][0] > 1:
                    lvl, t, v = lines[i]
                    if t == "DATE":
                        data["birth"] = _parse_date(v)
                    elif t == "PLAC":
                        data["birth_place"] = v
                    i += 1
                continue
            elif tag == "DEAT":
                i += 1
                while i < len(lines) and lines[i][0] > 1:
                    lvl, t, v = lines[i]
                    if t == "DATE":
                        data["death"] = _parse_date(v)
                    elif t == "PLAC":
                        data["death_place"] = v
                    i += 1
                continue
        i += 1
    return data, i


def _parse_fam_record(lines: List[Tuple[int, str, str]], start: int) -> Tuple[dict, int]:
    """Parse FAM record for basic family data. Returns (data, next_index)."""
    data = {
        "marriage": None,
        "marriage_place": "",
    }
    i = start
    while i < len(lines):
        level, tag, value = lines[i]
        if level == 0:
            break
        if level == 1 and tag == "MARR":
            i += 1
            while i < len(lines) and lines[i][0] > 1:
                lvl, t, v = lines[i]
                if t == "DATE":
                    data["marriage"] = _parse_date(v)
                elif t == "PLAC":
                    data["marriage_place"] = v
                i += 1
            continue
        i += 1
    return data, i


def _link_indi_record(db: Database, indi_map: Dict[str, int], fam_map: Dict[str, int], xref: str, lines: List, start: int):
    """Link INDI FAMS/FAMC references."""
    pid = indi_map.get(xref)
    if pid is None:
        return
    person = db.get_person(pid)
    if person is None:
        return
    i = start
    while i < len(lines):
        level, tag, value = lines[i]
        if level == 0:
            break
        if level == 1:
            if tag == "FAMS":
                fam_xref = value.strip()
                fid = fam_map.get(fam_xref)
                if fid is not None:
                    fam = db.get_family(fid)
                    if fam and fam not in person.families_as_parent:
                        person.families_as_parent.append(fam)
            elif tag == "FAMC":
                fam_xref = value.strip()
                fid = fam_map.get(fam_xref)
                if fid is not None:
                    fam = db.get_family(fid)
                    if fam:
                        if person.ascend is None:
                            person.ascend = Ascend(parents=fam)
                        else:
                            person.ascend.parents = fam
        i += 1


def _link_fam_record(db: Database, indi_map: Dict[str, int], fam_map: Dict[str, int], xref: str, lines: List, start: int):
    """Link FAM HUSB/WIFE/CHIL references."""
    fid = fam_map.get(xref)
    if fid is None:
        return
    fam = db.get_family(fid)
    if fam is None:
        return
    i = start
    while i < len(lines):
        level, tag, value = lines[i]
        if level == 0:
            break
        if level == 1:
            if tag == "CHIL":
                indi_xref = value.strip()
                cpid = indi_map.get(indi_xref)
                if cpid is not None:
                    child = db.get_person(cpid)
                    if child and child not in fam.children:
                        fam.children.append(child)
        i += 1


def _skip_record(lines: List[Tuple[int, str, str]], start: int) -> int:
    """Skip to the next 0-level record."""
    i = start
    while i < len(lines) and lines[i][0] != 0:
        i += 1
    return i
