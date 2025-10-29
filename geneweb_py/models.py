from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import uuid


def _new_id() -> str:
    return str(uuid.uuid4())


@dataclass
class CDate:
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    precision: Optional[str] = None  # 'year'|'month'|'day' or None

    def to_dict(self) -> Dict[str, Any]:
        return {"year": self.year, "month": self.month, "day": self.day, "precision": self.precision}

    @staticmethod
    def from_dict(d: Optional[Dict[str, Any]]) -> Optional["CDate"]:
        if not d:
            return None
        return CDate(year=d.get("year"), month=d.get("month"), day=d.get("day"), precision=d.get("precision"))

    def to_iso(self) -> Optional[str]:
        if not self or self.year is None:
            return None
        if self.month is None:
            return f"{self.year}"
        if self.day is None:
            return f"{self.year:04d}-{self.month:02d}"
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"

    @staticmethod
    def from_string(s: Optional[str]) -> Optional["CDate"]:
        if not s:
            return None
        raw = s.strip()
        if not raw:
            return None
        txt = raw.upper().strip()
        # ISO formats: YYYY or YYYY-MM or YYYY-MM-DD
        import re

        iso_match = re.match(r"^(\d{3,4})(?:-(\d{1,2})(?:-(\d{1,2}))?)?$", txt)
        if iso_match:
            year = int(iso_match.group(1))
            month = int(iso_match.group(2)) if iso_match.group(2) else None
            day = int(iso_match.group(3)) if iso_match.group(3) else None
            precision = "day" if day else "month" if month else "year"
            return CDate(year=year, month=month, day=day, precision=precision)

        # Month name formats like '12 JAN 1900' or 'JAN 1900'
        months = {
            "JAN": 1,
            "FEB": 2,
            "MAR": 3,
            "APR": 4,
            "MAY": 5,
            "JUN": 6,
            "JUL": 7,
            "AUG": 8,
            "SEP": 9,
            "SEPT": 9,
            "OCT": 10,
            "NOV": 11,
            "DEC": 12,
        }
        m = re.match(r"^(?:(\d{1,2})\s+)?([A-Z]{3,9})\.?,?\s+(\d{3,4})$", txt)
        if m:
            day = int(m.group(1)) if m.group(1) else None
            mon_txt = m.group(2)[:3]
            month = months.get(mon_txt)
            # only accept this match if the token is a valid month name
            if month:
                year = int(m.group(3))
                precision = "day" if day else "month"
                return CDate(year=year, month=month, day=day, precision=precision)

        # GEDCOM qualifiers: ABT/ABOUT/EST/CA -> approximate
        m = re.match(r"^(ABT|ABOUT|EST|CA|CIRCA)\.?\s+(\d{3,4})$", txt)
        if m:
            year = int(m.group(2))
            return CDate(year=year, month=None, day=None, precision="approx")

        # BETWEEN x AND y  or BET x AND y
        m = re.match(r"^(BET|BETWEEN)\s+(\d{3,4})\s+AND\s+(\d{3,4})$", txt)
        if m:
            lo = int(m.group(2))
            hi = int(m.group(3))
            # store lower bound and mark as range
            return CDate(year=lo, month=None, day=None, precision=f"between_{hi}")

        # FROM x TO y
        m = re.match(r"^FROM\s+(\d{3,4})\s+TO\s+(\d{3,4})$", txt)
        if m:
            lo = int(m.group(1))
            hi = int(m.group(2))
            return CDate(year=lo, month=None, day=None, precision=f"range_{hi}")

        # BEFORE / BEF
        m = re.match(r"^(BEF|BEFORE)\s+(\d{3,4})$", txt)
        if m:
            year = int(m.group(2))
            return CDate(year=year, precision="before")

        # AFTER / AFT
        m = re.match(r"^(AFT|AFTER)\s+(\d{3,4})$", txt)
        if m:
            year = int(m.group(2))
            return CDate(year=year, precision="after")

        # Fallback: find first 3-4 digit year in string
        m = re.search(r"(\d{3,4})", txt)
        if m:
            year = int(m.group(1))
            return CDate(year=year, precision="unknown")

        return None


@dataclass
class Place:
    town: Optional[str] = None
    county: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    other: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: Optional[Dict[str, Any]]) -> Optional["Place"]:
        if not d:
            return None
        return Place(town=d.get("town"), county=d.get("county"), state=d.get("state"), country=d.get("country"), other=d.get("other"))

    def to_simple(self) -> Optional[str]:
        # return a simple single-line place representation
        for v in (self.town, self.other, self.county, self.state, self.country):
            if v:
                return v
        return None

    @staticmethod
    def from_simple(s: Optional[str]) -> Optional["Place"]:
        if not s:
            return None
        return Place(other=s, town=s)


@dataclass
class PersEvent:
    kind: str
    date: Optional[CDate] = None
    place: Optional[Place] = None
    note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "date": self.date.to_dict() if self.date else None, "place": self.place.to_dict() if self.place else None, "note": self.note}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "PersEvent":
        return PersEvent(kind=d.get("kind", ""), date=CDate.from_dict(d.get("date")), place=Place.from_dict(d.get("place")), note=d.get("note"))


@dataclass
class Family:
    id: str = field(default_factory=_new_id)
    husband_id: Optional[str] = None
    wife_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    fevents: List[PersEvent] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "husband_id": self.husband_id, "wife_id": self.wife_id, "children_ids": self.children_ids, "fevents": [e.to_dict() for e in self.fevents]}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Family":
        evs = [PersEvent.from_dict(e) for e in d.get("fevents", [])]
        return Family(id=d.get("id", _new_id()), husband_id=d.get("husband_id"), wife_id=d.get("wife_id"), children_ids=d.get("children_ids", []), fevents=evs)


@dataclass
class Person:
    id: str = field(default_factory=_new_id)
    first_name: str = ""
    surname: str = ""
    # sex stored as string everywhere: 'M', 'F', 'N' or None
    sex: Optional[str] = None
    birth_date: Optional[CDate] = None
    birth_place: Optional[Place] = None
    birth_note: Optional[str] = None
    death_date: Optional[CDate] = None
    death_place: Optional[Place] = None
    death_note: Optional[str] = None
    pevents: List[PersEvent] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "first_name": self.first_name,
            "surname": self.surname,
            "sex": self.sex,
            "birth_date": self.birth_date.to_dict() if self.birth_date else None,
            "birth_place": self.birth_place.to_dict() if self.birth_place else None,
            "birth_note": self.birth_note,
            "death_date": self.death_date.to_dict() if self.death_date else None,
            "death_place": self.death_place.to_dict() if self.death_place else None,
            "death_note": self.death_note,
            "pevents": [e.to_dict() for e in self.pevents],
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Person":
        bd = d.get("birth_date")
        dp = d.get("death_date")
        return Person(
            id=d.get("id", _new_id()),
            first_name=d.get("first_name", ""),
            surname=d.get("surname", ""),
            sex=d.get("sex"),
            birth_date=CDate.from_dict(bd) if isinstance(bd, dict) else (bd if isinstance(bd, CDate) else None),
            birth_place=Place.from_dict(d.get("birth_place")) if isinstance(d.get("birth_place"), dict) else (d.get("birth_place") if isinstance(d.get("birth_place"), Place) else None),
            birth_note=d.get("birth_note"),
            death_date=CDate.from_dict(dp) if isinstance(dp, dict) else (dp if isinstance(dp, CDate) else None),
            death_place=Place.from_dict(d.get("death_place")) if isinstance(d.get("death_place"), dict) else (d.get("death_place") if isinstance(d.get("death_place"), Place) else None),
            death_note=d.get("death_note"),
            pevents=[PersEvent.from_dict(e) for e in d.get("pevents", [])],
            notes=d.get("notes", []),
        )


@dataclass
class Note:
    id: str = field(default_factory=_new_id)
    title: str = ""
    text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Note":
        return Note(id=d.get("id", _new_id()), title=d.get("title", ""), text=d.get("text", ""))
