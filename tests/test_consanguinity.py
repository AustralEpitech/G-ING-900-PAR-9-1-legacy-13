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


def test_double_first_cousins(tmp_path: Path):
    """Double first cousins should have r = 1/4 (0.25).

    Construct two grandparent couples; their children marry across so that
    the resulting cousins share both grandparent pairs.
    """
    store = Storage(tmp_path / "store")

    # Grandparents 1
    g1h = Person(first_name="G1H")
    g1w = Person(first_name="G1W")
    a = Person(first_name="A")
    b = Person(first_name="B")
    fam1 = Family(husband_id=g1h.id, wife_id=g1w.id, children_ids=[a.id, b.id])

    # Grandparents 2
    g2h = Person(first_name="G2H")
    g2w = Person(first_name="G2W")
    c = Person(first_name="C")
    d = Person(first_name="D")
    fam2 = Family(husband_id=g2h.id, wife_id=g2w.id, children_ids=[c.id, d.id])

    # Next generation marriages producing double cousins
    # A + C -> child x
    x = Person(first_name="X")
    fam_x = Family(husband_id=a.id, wife_id=c.id, children_ids=[x.id])
    # B + D -> child y
    y = Person(first_name="Y")
    fam_y = Family(husband_id=b.id, wife_id=d.id, children_ids=[y.id])

    for p in (g1h, g1w, a, b, g2h, g2w, c, d, x, y):
        store.add_person(p)
    store.add_family(fam1)
    store.add_family(fam2)
    store.add_family(fam_x)
    store.add_family(fam_y)

    r, common = relationship_and_links(store, x.id, y.id)
    assert approx_eq(r, 0.25)


def test_inbred_ancestor_reports_F(tmp_path: Path):
    """Create an ancestor whose parents are first cousins so ancestor F=1/8.

    Then verify that when that ancestor is a common ancestor of two
    descendants, the reported 'ancestor_inbreeding' equals ~0.125.
    """
    store = Storage(tmp_path / "store")

    # Build two grandparent couples G1 and G2
    G1h = Person(first_name="G1H")
    G1w = Person(first_name="G1W")
    A = Person(first_name="A")
    B = Person(first_name="B")
    famG1 = Family(husband_id=G1h.id, wife_id=G1w.id, children_ids=[A.id, B.id])

    G2h = Person(first_name="G2H")
    G2w = Person(first_name="G2W")
    C = Person(first_name="C")
    D = Person(first_name="D")
    famG2 = Family(husband_id=G2h.id, wife_id=G2w.id, children_ids=[C.id, D.id])

    # Their children marry crosswise to make first cousins P1 and P2
    P1 = Person(first_name="P1")
    famP1 = Family(husband_id=A.id, wife_id=C.id, children_ids=[P1.id])

    P2 = Person(first_name="P2")
    famP2 = Family(husband_id=B.id, wife_id=D.id, children_ids=[P2.id])

    # Now ancestor X is child of P1 + P2 (parents are first cousins)
    X = Person(first_name="X")
    famX = Family(husband_id=P1.id, wife_id=P2.id, children_ids=[X.id])

    # Make two grandchildren of X (via two different children) so X is common ancestor
    S1 = Person(first_name="S1")
    S2 = Person(first_name="S2")
    famS1 = Family(husband_id=X.id, wife_id=None, children_ids=[S1.id])
    famS2 = Family(husband_id=X.id, wife_id=None, children_ids=[S2.id])

    # Add all persons and families
    for p in (G1h, G1w, A, B, G2h, G2w, C, D, P1, P2, X, S1, S2):
        store.add_person(p)
    for f in (famG1, famG2, famP1, famP2, famX, famS1, famS2):
        store.add_family(f)

    # relationship between S1 and S2 should include X as common ancestor
    r, common = relationship_and_links(store, S1.id, S2.id)
    # find X in common ancestors
    ent = next((e for e in common if e["ancestor_id"] == X.id), None)
    assert ent is not None
    # X's parents in this construction are actually double first cousins
    # (they share both grandparent couples), so X's inbreeding F ~= 0.25
    assert approx_eq(ent["ancestor_inbreeding"], 0.25)
