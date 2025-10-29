from geneweb_py.search import search_people, search_families
from geneweb_py.storage import Storage
from geneweb_py.models import Person, Family


def test_search_people_basic(tmp_path):
    st = Storage(tmp_path)
    p1 = Person(first_name="John", surname="Doe")
    p2 = Person(first_name="Johnny", surname="Smith")
    p3 = Person(first_name="Jane", surname="Doe")
    st.add_person(p1)
    st.add_person(p2)
    st.add_person(p3)

    res = search_people(list(st.list_persons()), "john")
    # Expect John Doe first, then Johnny Smith (both match 'john' but exact is ranked higher)
    assert len(res) >= 2
    assert res[0].id == p1.id
    assert any(r.id == p2.id for r in res)


def test_search_families_basic(tmp_path):
    st = Storage(tmp_path)
    h = Person(first_name="H", surname="Doe")
    w = Person(first_name="W", surname="Smith")
    st.add_person(h)
    st.add_person(w)
    f = Family(husband_id=h.id, wife_id=w.id, children_ids=[])
    st.add_family(f)

    res = search_families(list(st.families.values()), list(st.list_persons()), "doe")
    assert len(res) == 1
    assert res[0].id == f.id
