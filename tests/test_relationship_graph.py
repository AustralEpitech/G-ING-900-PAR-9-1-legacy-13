from pathlib import Path
from geneweb_py.models import Person, Family
from geneweb_py.storage import Storage
from geneweb_py.relationship import shortest_path, all_shortest_paths


def test_shortest_path_parent_child(tmp_path: Path):
    store = Storage(tmp_path / "s")
    parent = Person(first_name="Parent")
    child = Person(first_name="Child")
    fam = Family(husband_id=parent.id, wife_id=None, children_ids=[child.id])
    store.add_person(parent)
    store.add_person(child)
    store.add_family(fam)

    dist, path = shortest_path(store, parent.id, child.id)
    assert dist == 1
    assert path == [parent.id, child.id]


def test_shortest_path_siblings(tmp_path: Path):
    store = Storage(tmp_path / "s")
    father = Person(first_name="F")
    mother = Person(first_name="M")
    s1 = Person(first_name="S1")
    s2 = Person(first_name="S2")
    fam = Family(husband_id=father.id, wife_id=mother.id, children_ids=[s1.id, s2.id])
    for p in (father, mother, s1, s2):
        store.add_person(p)
    store.add_family(fam)

    dist, path = shortest_path(store, s1.id, s2.id)
    assert dist == 2
    assert path[0] == s1.id and path[-1] == s2.id
    assert len(path) == 3

    # there should be two distinct shortest paths via father and via mother
    paths = all_shortest_paths(store, s1.id, s2.id, max_paths=10)
    # convert paths to tuples for easy comparison
    tupaths = {tuple(p) for p in paths}
    expected1 = (s1.id, father.id, s2.id)
    expected2 = (s1.id, mother.id, s2.id)
    assert expected1 in tupaths
    assert expected2 in tupaths


def test_shortest_path_unrelated(tmp_path: Path):
    store = Storage(tmp_path / "s")
    a = Person(first_name="A")
    b = Person(first_name="B")
    store.add_person(a)
    store.add_person(b)
    dist, path = shortest_path(store, a.id, b.id)
    assert dist is None
    assert path == []
