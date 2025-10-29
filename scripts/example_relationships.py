"""Small example script that demonstrates relationship utilities.

Creates a tiny pedigree inside `data/example_demo` and prints:
 - Sosa (Ahnentafel) ancestors for the root
 - a shortest path between two persons
 - coefficient of relationship and common ancestors
 - an example cousin label

Run:
    python scripts/example_relationships.py
"""
from pathlib import Path
from pprint import pprint
import sys

# Ensure repo root is on sys.path when running this script directly
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from geneweb_py.storage import Storage
from geneweb_py.models import Person, Family
from geneweb_py.sosa import sosa_ancestors
from geneweb_py.relationship import shortest_path
from geneweb_py.consanguinity import relationship_and_links
from geneweb_py.cousins import cousin_label


def build_demo(store: Storage):
    # Simple pedigree (same as tests): A <- B+C; B <- D+E; C <- F+G
    A = Person(first_name="A")
    B = Person(first_name="B")
    C = Person(first_name="C")
    D = Person(first_name="D")
    E = Person(first_name="E")
    F = Person(first_name="F")
    G = Person(first_name="G")

    fam_B = Family(husband_id=D.id, wife_id=E.id, children_ids=[B.id])
    fam_C = Family(husband_id=F.id, wife_id=G.id, children_ids=[C.id])
    fam_A = Family(husband_id=B.id, wife_id=C.id, children_ids=[A.id])

    for p in (A, B, C, D, E, F, G):
        store.add_person(p)
    store.add_family(fam_B)
    store.add_family(fam_C)
    store.add_family(fam_A)
    return A, B, C, D, E, F, G


def main():
    data_dir = Path("data") / "example_demo"
    store = Storage(data_dir)

    A, B, C, D, E, F, G = build_demo(store)

    print("Sosa ancestors for A:")
    anc = sosa_ancestors(store, A.id, max_depth=3)
    # pretty print each ancestor with name and sosa
    for e in anc:
        pid = e["person_id"]
        p = store.get_person(pid)
        print(f"  {e['sosa']:>3}: {p.first_name} (id={pid[:8]})")

    print("\nShortest path D -> G:")
    dist, path = shortest_path(store, D.id, G.id)
    print(f"  distance={dist}")
    print("  path:")
    for pid in path:
        print("   -", store.get_person(pid).first_name)

    print("\nCoefficient of relationship A <-> B:")
    r, common = relationship_and_links(store, A.id, B.id, max_anc_depth=6)
    print(f"  r = {r:.6f}")
    print("  common ancestors:")
    pprint(common)

    print("\nCousin label example (l1=2, l2=3):")
    label, degree, removed = cousin_label(2, 3)
    print(f"  {label} (degree={degree}, removed={removed})")


if __name__ == "__main__":
    main()
