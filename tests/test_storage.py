from pathlib import Path
from geneweb_py.storage import Storage
from geneweb_py.models import Person, Family, Note


def test_person_crud_and_listing(tmp_path):
    sroot = tmp_path / "data"
    st = Storage(sroot)
    p = Person(first_name="P1")
    st.add_person(p)
    assert st.get_person(p.id).first_name == "P1"
    assert len(st.list_persons()) == 1


def test_family_indexing(tmp_path):
    st = Storage(tmp_path)
    p1 = Person(first_name="H")
    p2 = Person(first_name="W")
    st.add_person(p1)
    st.add_person(p2)
    f = Family(husband_id=p1.id, wife_id=p2.id, children_ids=[])
    st.add_family(f)
    fams = list(st.families_of_person(p1.id))
    assert len(fams) == 1 and fams[0].id == f.id


def test_notes_commit_and_list_and_files(tmp_path):
    st = Storage(tmp_path)
    st.commit_note("n1", "T1", "body1")
    # file should exist
    p = st.note_file_path("n1")
    assert p.exists()
    n = st.get_note("n1")
    assert n and n.text == "body1"
    # list_notes should yield it
    ids = [x.id for x in st.list_notes()]
    assert "n1" in ids


def test_delete_note(tmp_path):
    st = Storage(tmp_path)
    st.commit_note("n2", "T2", "b2")
    assert st.delete_note("n2")
    assert st.get_note("n2") is None


def test_update_and_delete_person_affects_families(tmp_path):
    st = Storage(tmp_path)
    p1 = Person(first_name="A")
    p2 = Person(first_name="B")
    st.add_person(p1)
    st.add_person(p2)
    f = Family(husband_id=p1.id, wife_id=p2.id, children_ids=[p2.id])
    st.add_family(f)
    # delete p2 should remove references from family
    assert st.delete_person(p2.id)
    fam = st.get_family(f.id)
    assert fam.husband_id == p1.id
    assert fam.wife_id is None


def test_update_family_and_delete_family(tmp_path):
    st = Storage(tmp_path)
    p1 = Person(first_name="A")
    st.add_person(p1)
    f = Family(husband_id=p1.id, wife_id=None, children_ids=[])
    st.add_family(f)
    f.husband_id = None
    st.update_family(f)
    assert st.get_family(f.id).husband_id is None
    assert st.delete_family(f.id)
    assert st.get_family(f.id) is None


def test_update_person_raises_on_missing(tmp_path):
    st = Storage(tmp_path)
    p = Person()
    try:
        st.update_person(p)
        raised = False
    except KeyError:
        raised = True
    assert raised
