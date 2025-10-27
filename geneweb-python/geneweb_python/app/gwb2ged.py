from __future__ import annotations

from io import StringIO
from typing import TextIO, Optional

try:
    # Reuse the existing Database and models if available in the workspace
    from core.database import Database
except Exception as exc:  # pragma: no cover - fallback error message
    raise RuntimeError(
        "core.database.Database not found. Ensure you run from the repo root or adjust imports."
    ) from exc


def _fmt_date(cdate) -> Optional[str]:
    """Return GEDCOM-like DATE string from CDate-like object if present.

    Accepts objects with attributes: year, month, day (all optional/int).
    GEDCOM format (simplified): 'DD MON YYYY' | 'MON YYYY' | 'YYYY'
    """
    if not cdate:
        return None
    year = getattr(cdate, "year", None)
    month = getattr(cdate, "month", None)
    day = getattr(cdate, "day", None)
    months = [
        None,
        "JAN",
        "FEB",
        "MAR",
        "APR",
        "MAY",
        "JUN",
        "JUL",
        "AUG",
        "SEP",
        "OCT",
        "NOV",
        "DEC",
    ]
    if year and month and day:
        return f"{day:02d} {months[month]} {year}"
    if year and month:
        return f"{months[month]} {year}"
    if year:
        return f"{year}"
    return None


def export_gedcom(db: Database, out: TextIO) -> None:
    """Export a minimal GEDCOM from the Database to the given text stream.

    This is a starter implementation: it writes HEAD, INDI (persons), and FAM (families)
    with minimal properties. It aims to be valid and parsable by basic GEDCOM readers
    and can be extended to reach full parity.
    """
    # Header
    out.write("0 HEAD\n")
    out.write("1 SOUR geneweb-python\n")
    out.write("1 GEDC\n")
    out.write("2 VERS 5.5\n")
    out.write("2 FORM LINEAGE-LINKED\n")
    out.write("1 CHAR UTF-8\n")

    # Build reverse lookup maps from object -> ids
    persons = getattr(db, "persons", {}) or {}
    families = getattr(db, "families", {}) or {}
    person_id_by_obj = {obj: pid for pid, obj in persons.items()}
    family_id_by_obj = {obj: fid for fid, obj in families.items()}

    # INDI records
    for pid, person in persons.items():
        out.write(f"0 @I{pid}@ INDI\n")
        first = getattr(person, "first_name", "")
        last = getattr(person, "surname", "")
        # GEDCOM expects slashes around surname
        out.write(f"1 NAME {first} /{last}/\n")

        sex = getattr(person, "sex", "").upper()[:1]
        if sex in {"M", "F"}:
            out.write(f"1 SEX {sex}\n")

        birth = getattr(person, "birth", None)
        if birth:
            out.write("1 BIRT\n")
            date_str = _fmt_date(birth)
            if date_str:
                out.write(f"2 DATE {date_str}\n")
            place = getattr(person, "birth_place", None)
            if place:
                out.write(f"2 PLAC {place}\n")

        death = getattr(person, "death", None)
        if death:
            out.write("1 DEAT\n")
            date_str = _fmt_date(death)
            if date_str:
                out.write(f"2 DATE {date_str}\n")
            place = getattr(person, "death_place", None)
            if place:
                out.write(f"2 PLAC {place}\n")

        # FAMS: families where this person is a parent
        for fam in getattr(person, "families_as_parent", []) or []:
            fid = family_id_by_obj.get(fam)
            if fid is not None:
                out.write(f"1 FAMS @F{fid}@\n")

        # FAMC: family where this person is a child (from ascend.parents)
        ascend = getattr(person, "ascend", None)
        if ascend is not None:
            parents_fam = getattr(ascend, "parents", None)
            if parents_fam is not None:
                fid = family_id_by_obj.get(parents_fam)
                if fid is not None:
                    out.write(f"1 FAMC @F{fid}@\n")

    # FAM records (minimal; members may require more linkage in core models)
    for fid, family in families.items():
        out.write(f"0 @F{fid}@ FAM\n")
        marriage = getattr(family, "marriage", None)
        if marriage:
            out.write("1 MARR\n")
            date_str = _fmt_date(marriage)
            if date_str:
                out.write(f"2 DATE {date_str}\n")
            place = getattr(family, "marriage_place", None)
            if place:
                out.write(f"2 PLAC {place}\n")

        # Determine parents: find persons where family is in families_as_parent
        parents = []
        for p in persons.values():
            fams = getattr(p, "families_as_parent", []) or []
            if family in fams:
                parents.append(p)

        # Assign HUSB/WIFE by sex if possible
        husband_written = False
        wife_written = False
        for p in parents:
            pid = person_id_by_obj.get(p)
            if pid is None:
                continue
            sex = (getattr(p, "sex", "") or "").upper()[:1]
            if sex == "M" and not husband_written:
                out.write(f"1 HUSB @I{pid}@\n")
                husband_written = True
            elif sex == "F" and not wife_written:
                out.write(f"1 WIFE @I{pid}@\n")
                wife_written = True

        # If sex not set or single parent, still output at least one parent as HUSB
        remaining = [p for p in parents if person_id_by_obj.get(p) is not None]
        if not husband_written and remaining:
            pid = person_id_by_obj[remaining[0]]
            out.write(f"1 HUSB @I{pid}@\n")
            husband_written = True
            remaining = remaining[1:]
        if not wife_written and remaining:
            pid = person_id_by_obj[remaining[0]]
            out.write(f"1 WIFE @I{pid}@\n")
            wife_written = True

        # Children
        for child in getattr(family, "children", []) or []:
            cpid = person_id_by_obj.get(child)
            if cpid is not None:
                out.write(f"1 CHIL @I{cpid}@\n")

    # Trailer
    out.write("0 TRLR\n")


def export_gedcom_to_string(db: Database) -> str:
    buf = StringIO()
    export_gedcom(db, buf)
    return buf.getvalue()
