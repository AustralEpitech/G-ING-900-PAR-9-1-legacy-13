import os
from pathlib import Path

from geneweb_py.web import app as web_app
from geneweb_py.web.app import create_person, create_family
from geneweb_py.storage import Storage
from geneweb_py.models import Person


def test_person_create_form_persists(tmp_path):
    # Use an isolated data directory for storage
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    storage = Storage(data_dir)
    # swap the app storage to the test storage and restore afterwards
    original = getattr(web_app, "storage", None)
    web_app.storage = storage

    # simulate submit of person create form fields via direct handler call
    first_name = "Test"
    surname = "User"
    sex = "M"
    # single event via repeated fields
    pevent_kind = ["BAPTISM"]
    pevent_date = ["12 JAN 1900"]
    pevent_place = ["St Mary\'s"]
    pevent_note = ["Notes"]

    # call the handler directly (it will add to storage)
    resp = create_person(
        first_name=first_name,
        surname=surname,
        sex=sex,
        birth_date=None,
        birth_place=None,
        birth_note=None,
        death_date=None,
        death_place=None,
        death_note=None,
        pevent_kind=pevent_kind,
        pevent_date=pevent_date,
        pevent_place=pevent_place,
        pevent_note=pevent_note,
    )

    try:
        # storage should contain exactly one person with given name
        persons = list(storage.list_persons())
        assert any(p.first_name == first_name and p.surname == surname for p in persons)
        p = next(p for p in persons if p.first_name == first_name and p.surname == surname)
        assert len(p.pevents) == 1
        ev = p.pevents[0]
        assert ev.kind == "BAPTISM"
        assert ev.note == "Notes"
    finally:
        # restore original app storage to avoid leaking into other tests
        if original is not None:
            web_app.storage = original
        else:
            delattr(web_app, "storage")


def test_family_create_form_persists(tmp_path):
    data_dir = tmp_path / "data2"
    data_dir.mkdir()
    storage = Storage(data_dir)
    original = getattr(web_app, "storage", None)
    web_app.storage = storage

    # create two people to reference
    a = Person(first_name="H1", surname="S1", sex="M")
    b = Person(first_name="W1", surname="S2", sex="F")
    storage.add_person(a)
    storage.add_person(b)

    # family event fields
    fevent_kind = ["MARRIAGE"]
    fevent_date = ["1 JUN 1920"]
    fevent_place = ["Town Hall"]
    fevent_note = ["Civil ceremony"]

    try:
        # call family create handler
        create_family(husband_id=a.id, wife_id=b.id, children_ids=[], fevent_kind=fevent_kind, fevent_date=fevent_date, fevent_place=fevent_place, fevent_note=fevent_note)

        # check families persisted
        fams = list(storage.families.values())
        assert len(fams) == 1
        fam = fams[0]
        assert fam.husband_id == a.id
        assert fam.wife_id == b.id
        assert len(fam.fevents) == 1
        ev = fam.fevents[0]
        assert ev.kind == "MARRIAGE"
        assert ev.note == "Civil ceremony"
    finally:
        # restore original storage
        if original is not None:
            web_app.storage = original
        else:
            delattr(web_app, "storage")
