"""Consanguinity / coefficient-of-relationship utilities.

Provides functions to compute the coefficient of relationship between two
persons (including implex by counting multiple ancestor paths) and to report
the contributing common ancestors and their per-path counts.

API:
    relationship_and_links(storage, a_id, b_id, max_anc_depth=None)

The implementation counts distinct ancestor-to-person upward paths by
generation length (bounded by max_anc_depth) and sums contributions using
the classic formula:

    r = sum_ancestors sum_{paths to A, paths to B} (1/2)^(n1+n2) * (1 + F_anc)

Where F_anc is the inbreeding coefficient of the ancestor (computed
recursively when possible). We memoize inbreeding coefficients to avoid
redundant work.
"""
from __future__ import annotations
from collections import defaultdict, deque
from typing import Dict, Optional, Tuple, List


def _parents_of(storage, pid: str) -> List[str]:
    """Return a list of parent ids for pid (may be empty)."""
    parents = []
    try:
        for fam in storage.families_of_person(pid):
            # if pid appears as a child in this family, the husband/wife are parents
            if pid in getattr(fam, "children_ids", []):
                if getattr(fam, "husband_id", None):
                    parents.append(fam.husband_id)
                if getattr(fam, "wife_id", None):
                    parents.append(fam.wife_id)
    except Exception:
        return []
    # remove possible None and duplicates
    return [p for i, p in enumerate(parents) if p and p not in parents[:i]]


def _ancestor_path_counts(storage, pid: str, max_depth: Optional[int]) -> Dict[str, Dict[int, int]]:
    """Count upward ancestor paths from pid.

    Returns a mapping ancestor_id -> {distance: count} where distance is the
    number of generations from ancestor -> pid. The mapping includes the pid
    itself at distance 0 with count 1.
    """
    if max_depth is None:
        max_depth = 10  # sane default

    counts: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
    # level propagation: start with the person at depth 0
    current: Dict[str, int] = {pid: 1}
    counts[pid][0] = 1

    for depth in range(0, max_depth):
        if not current:
            break
        next_level: Dict[str, int] = {}
        for node, ways in current.items():
            parents = _parents_of(storage, node)
            for p in parents:
                # increment the number of distinct upward paths reaching p at depth+1
                counts[p][depth + 1] += ways
                next_level[p] = next_level.get(p, 0) + ways
        current = next_level

    return counts


def relationship_and_links(storage, a_id: str, b_id: str, max_anc_depth: Optional[int] = None) -> Tuple[float, List[dict]]:
    """Compute coefficient of relationship r between persons a and b.

    Returns (r, common_ancestors) where common_ancestors is a list of dicts
    describing for each ancestor: ancestor_id, n1_counts, n2_counts,
    contribution, ancestor_inbreeding.
    """
    # Quick validation
    if a_id is None or b_id is None:
        return 0.0, []
    if a_id not in storage.persons or b_id not in storage.persons:
        return 0.0, []

    # Precompute ancestor path counts (including self at distance 0)
    a_counts = _ancestor_path_counts(storage, a_id, max_anc_depth)
    b_counts = _ancestor_path_counts(storage, b_id, max_anc_depth)

    # Memoization for inbreeding coefficients
    f_memo: Dict[str, float] = {}
    computing: set = set()

    def _inbreeding(person_id: str) -> float:
        """Compute inbreeding coefficient F_person (memoized)."""
        if person_id in f_memo:
            return f_memo[person_id]
        if person_id in computing:
            # cycle detection: defensively treat as 0 while computing
            return 0.0
        computing.add(person_id)
        parents = _parents_of(storage, person_id)
        if len(parents) >= 2:
            # relationship between parents approximates F(child)
            r_parents, _ = relationship_and_links(storage, parents[0], parents[1], max_anc_depth)
            F = r_parents
        else:
            F = 0.0
        f_memo[person_id] = F
        computing.remove(person_id)
        return F

    # Find common ancestors
    common = set(a_counts.keys()) & set(b_counts.keys())
    if not common:
        return 0.0, []

    total_r = 0.0
    common_list: List[dict] = []
    for anc in sorted(common):
        # build depth->count dictionaries
        n1_counts = dict(a_counts.get(anc, {}))
        n2_counts = dict(b_counts.get(anc, {}))
        Fanc = _inbreeding(anc)
        contrib = 0.0
        for n1, c1 in n1_counts.items():
            for n2, c2 in n2_counts.items():
                contrib += (c1 * c2) * (0.5 ** (n1 + n2))
        contrib *= (1.0 + Fanc)
        if contrib > 0.0:
            total_r += contrib
            common_list.append({
                "ancestor_id": anc,
                "n1_counts": n1_counts,
                "n2_counts": n2_counts,
                "contribution": contrib,
                "ancestor_inbreeding": Fanc,
            })

    return total_r, common_list
