from pathlib import Path

from geneweb_py.storage import Storage
from geneweb_py.models import Person, Family
from geneweb_py.consanguinity import relationship_and_links


def approx_eq(a, b, eps=1e-9):
    return abs(a - b) <= eps


def test_parent_child(tmp_path: Path):
    store = Storage(tmp_path / "store")
    father = Person(first_name="F")
    child = Person(first_name="C")
    fam = Family(husband_id=father.id, wife_id=None, children_ids=[child.id])
    store.add_person(father)
    store.add_person(child)
    store.add_family(fam)

    r, common = relationship_and_links(store, father.id, child.id)
    assert approx_eq(r, 0.5)


def test_full_siblings(tmp_path: Path):
    store = Storage(tmp_path / "store")
    p = Person(first_name="P")
    q = Person(first_name="Q")
    a = Person(first_name="A")
    b = Person(first_name="B")
    fam_par = Family(husband_id=p.id, wife_id=q.id, children_ids=[a.id, b.id])
    for person in (p, q, a, b):
        store.add_person(person)
    store.add_family(fam_par)

    r, common = relationship_and_links(store, a.id, b.id)
    # full siblings (unrelated parents) -> r = 0.5
    assert approx_eq(r, 0.5)


def test_half_siblings(tmp_path: Path):
    store = Storage(tmp_path / "store")
    father = Person(first_name="F")
    m1 = Person(first_name="M1")
    m2 = Person(first_name="M2")
    c1 = Person(first_name="C1")
    c2 = Person(first_name="C2")

    fam1 = Family(husband_id=father.id, wife_id=m1.id, children_ids=[c1.id])
    fam2 = Family(husband_id=father.id, wife_id=m2.id, children_ids=[c2.id])
    for p in (father, m1, m2, c1, c2):
        store.add_person(p)
    store.add_family(fam1)
    store.add_family(fam2)

    r, common = relationship_and_links(store, c1.id, c2.id)
    # half-siblings -> r = 0.25
    assert approx_eq(r, 0.25)


def test_first_cousins(tmp_path: Path):
    store = Storage(tmp_path / "store")
    gp_h = Person(first_name="GP_H")
    gp_w = Person(first_name="GP_W")
    p = Person(first_name="P")
    q = Person(first_name="Q")
    a = Person(first_name="A")
    b = Person(first_name="B")

    fam_gp = Family(husband_id=gp_h.id, wife_id=gp_w.id, children_ids=[p.id, q.id])
    fam_p = Family(husband_id=p.id, wife_id=None, children_ids=[a.id])
    fam_q = Family(husband_id=q.id, wife_id=None, children_ids=[b.id])

    for pers in (gp_h, gp_w, p, q, a, b):
        store.add_person(pers)
    store.add_family(fam_gp)
    store.add_family(fam_p)
    store.add_family(fam_q)

    r, common = relationship_and_links(store, a.id, b.id)
    # first cousins -> r = 1/8 = 0.125
    assert approx_eq(r, 0.125)
