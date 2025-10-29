from pathlib import Path
import tempfile

from geneweb_py.storage import Storage
from geneweb_py.models import Person, Family
from geneweb_py.sosa import sosa_ancestors


def test_basic_sosa_tree(tmp_path: Path):
    # Setup a small pedigree:
    #    D   F
    #    E   G
    #     \ /
    #      B   C
    #       \ /
    #        A (root)
    root_dir = tmp_path / "store"
    store = Storage(root_dir)

    # Create persons
    A = Person(first_name="A")
    B = Person(first_name="B")
    C = Person(first_name="C")
    D = Person(first_name="D")
    E = Person(first_name="E")
    F = Person(first_name="F")
    G = Person(first_name="G")

    # Families: (B,E,D) means D+E -> B
    fam_B = Family(husband_id=D.id, wife_id=E.id, children_ids=[B.id])
    fam_C = Family(husband_id=F.id, wife_id=G.id, children_ids=[C.id])
    fam_A = Family(husband_id=B.id, wife_id=C.id, children_ids=[A.id])

    # Add to store
    for p in (A, B, C, D, E, F, G):
        store.add_person(p)
    store.add_family(fam_B)
    store.add_family(fam_C)
    store.add_family(fam_A)

    # Compute sosa
    anc = sosa_ancestors(store, A.id, max_depth=3)
    # Build mapping person_id -> sosa
    mp = {e["person_id"]: e["sosa"] for e in anc}

    # Check expected sosa numbers
    assert mp[A.id] == 1
    assert mp[B.id] == 2
    assert mp[C.id] == 3
    assert mp[D.id] == 4
    assert mp[E.id] == 5
    assert mp[F.id] == 6
    assert mp[G.id] == 7

    # Check that nb_families for B and C equals 1 and that A has parents
    entA = next(e for e in anc if e["person_id"] == A.id)
    entB = next(e for e in anc if e["person_id"] == B.id)
    entC = next(e for e in anc if e["person_id"] == C.id)
    assert entA["has_parents"] is True
    assert entB["nb_families"] == 1
    assert entC["nb_families"] == 1
