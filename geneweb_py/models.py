from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import date
import uuid
import json


def _new_id() -> str:
    return str(uuid.uuid4())


@dataclass
class Event:
    kind: str
    date: Optional[str] = None
    place: Optional[str] = None
    note: Optional[str] = None


@dataclass
class Person:
    id: str = field(default_factory=_new_id)
    first_name: str = ""
    surname: str = ""
    sex: Optional[str] = None  # 'M' | 'F' | None
    birth: Optional[Event] = None
    death: Optional[Event] = None
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Person":
        birth = Event(**d["birth"]) if d.get("birth") else None
        death = Event(**d["death"]) if d.get("death") else None
        return Person(
            id=d.get("id", _new_id()),
            first_name=d.get("first_name", ""),
            surname=d.get("surname", ""),
            sex=d.get("sex"),
            birth=birth,
            death=death,
            notes=d.get("notes", []),
        )


@dataclass
class Family:
    id: str = field(default_factory=_new_id)
    husband_id: Optional[str] = None
    wife_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Family":
        evs = [Event(**e) for e in d.get("events", [])]
        return Family(
            id=d.get("id", _new_id()),
            husband_id=d.get("husband_id"),
            wife_id=d.get("wife_id"),
            children_ids=d.get("children_ids", []),
            events=evs,
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
