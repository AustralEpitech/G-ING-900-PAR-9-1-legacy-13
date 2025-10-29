from geneweb_py.web.app import storage, api_create_person, api_family
from geneweb_py.models import Person, Family, PersEvent, CDate, Place


def test_api_create_person_with_pevents():
    payload = {
        "first_name": "Alice",
        "surname": "Smith",
        "sex": "F",
        "pevents": ["BAPTISM | 12 JAN 1900 | St Mary's Church | Baptized as infant"]
    }
    body = api_create_person(payload)
    assert body["first_name"] == "Alice"
    assert isinstance(body.get("pevents"), list)
    assert len(body["pevents"]) == 1
    ev = body["pevents"][0]
    assert ev["kind"] == "BAPTISM"
    assert ev["date"]["year"] == 1900
    assert ev["date"]["month"] == 1
    assert ev["date"]["day"] == 12
    assert ev["place"]["town"] == "St Mary's Church" or ev["place"]["other"] == "St Mary's Church"
    assert "Baptized" in (ev.get("note") or "")


def test_family_fevents_roundtrip():
    # create two persons in storage
    p1 = Person(first_name="Husband", surname="One", sex="M")
    p2 = Person(first_name="Wife", surname="Two", sex="F")
    storage.add_person(p1)
    storage.add_person(p2)

    # create a family with a fevent
    fe = PersEvent(kind="MARRIAGE", date=CDate.from_string("1 JUN 1920"), place=Place.from_simple("Town Hall"), note="Civil ceremony")
    fam = Family(husband_id=p1.id, wife_id=p2.id, children_ids=[], fevents=[fe])
    storage.add_family(fam)

    body = api_family(fam.id)
    assert "family" in body
    f = body["family"]
    assert isinstance(f.get("fevents"), list)
    assert len(f["fevents"]) == 1
    ev = f["fevents"][0]
    assert ev["kind"] == "MARRIAGE"
    # date returned as dict
    assert ev["date"]["year"] == 1920
    assert ev["place"]["other"] == "Town Hall" or ev["place"]["town"] == "Town Hall"
    assert ev["note"] == "Civil ceremony"
