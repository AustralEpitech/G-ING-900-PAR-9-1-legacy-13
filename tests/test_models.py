import json
from geneweb_py.models import Person, Family, Note, PersEvent, CDate, Place
import pytest


def test_person_to_from_dict():
    p = Person(first_name="Alice", surname="Smith", sex="F")
    d = p.to_dict()
    assert d["first_name"] == "Alice"
    p2 = Person.from_dict(d)
    assert p2.first_name == "Alice"
    assert p2.surname == "Smith"


def test_family_to_from_dict():
    f = Family(husband_id="h1", wife_id="w1", children_ids=["c1", "c2"])
    d = f.to_dict()
    assert d["husband_id"] == "h1"
    f2 = Family.from_dict(d)
    assert f2.children_ids == ["c1", "c2"]


def test_note_to_from_dict():
    n = Note(title="T", text="body")
    d = n.to_dict()
    assert d["title"] == "T"
    n2 = Note.from_dict(d)
    assert n2.text == "body"


def test_event_dataclass():
    e = PersEvent(kind="birth", date=CDate.from_string("2000-01-01"), place=Place.from_simple("Nowhere"), note="x")
    d = e.to_dict()
    assert d["kind"] == "birth"
    assert d["date"]["year"] == 2000
    assert d["place"]["other"] == "Nowhere"


@pytest.mark.parametrize(
    "s,expected",
    [
        ("ABT 1900", (1900, None, None, "approx")),
        ("BEF 1900", (1900, None, None, "before")),
        ("AFT 1900", (1900, None, None, "after")),
        ("BET 1900 AND 1910", (1900, None, None, "between_1910")),
        ("FROM 1890 TO 1900", (1890, None, None, "range_1900")),
        ("12 JAN 1900", (1900, 1, 12, "day")),
        ("JAN 1900", (1900, 1, None, "month")),
        ("1900-05-03", (1900, 5, 3, "day")),
        ("1900-05", (1900, 5, None, "month")),
        ("1900", (1900, None, None, "year")),
    ],
)
def test_cdate_from_string(s, expected):
    cd = CDate.from_string(s)
    assert cd is not None
    y, m, d, prec = expected
    assert cd.year == y
    assert cd.month == m
    assert cd.day == d
    assert cd.precision == prec


def test_cdate_fallback_year():
    cd = CDate.from_string("around 1875 or so")
    assert cd is not None
    assert cd.year == 1875
    assert cd.precision == "unknown"
