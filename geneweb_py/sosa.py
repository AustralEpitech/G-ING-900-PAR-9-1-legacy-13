"""Sosa (Ahnentafel) numbering utilities.

This module provides a minimal implementation of Sosa (Ahnentafel) numbering
suitable for the Python port. It enumerates ancestors and assigns Sosa numbers
(root=1, father=2*n, mother=2*n+1).

The implementation is conservative: it assigns the first-discovered parents for
persons with multiple parent families but records `nb_families` so callers can
notice multiple parent families. It also detects cycles and avoids infinite
loops.

API:
    sosa_ancestors(storage, root_id, max_depth=10) -> List[dict]

Each dict in the returned list contains at least the keys:
    - person_id: str
    - sosa: int
    - level: int (0 for root, 1 for parents, ...)
    - father_sosa: Optional[int]
    - mother_sosa: Optional[int]
    - has_parents: bool
    - nb_families: int

"""
from __future__ import annotations
from typing import List, Dict, Optional, Set, Tuple
from collections import deque


def _parents_of_person(storage, pid: str) -> Tuple[List[Optional[str]], int]:
    """Return (parents_pair_list, nb_families).

    parents_pair_list is a list with a single tuple (father_id, mother_id) for
    the first family where `pid` appears as a child. If no such family, the
    tuple is (None, None). nb_families is the total number of families where
    the person appears as a child.
    """
    families = list(storage.families_of_person(pid))
    # consider only families where pid is a child
    child_fams = [f for f in families if pid in getattr(f, "children_ids", [])]
    nb = len(child_fams)
    if nb == 0:
        return [(None, None)], 0
    # For now pick the first family as the canonical one for parents
    fam = child_fams[0]
    return [(fam.husband_id, fam.wife_id)], nb


def sosa_ancestors(storage, root_id: str, max_depth: int = 10) -> List[Dict]:
    """Enumerate ancestors starting from root_id and assign Sosa numbers.

    Returns a list of ancestor entries (including the root) with Sosa numbers and
    simple parent metadata. The traversal stops at `max_depth` generations.
    """
    if root_id is None:
        return []

    result: List[Dict] = []
    # mapping person_id -> assigned sosa number (first discovered)
    assigned: Dict[str, int] = {}

    # BFS queue of tuples (person_id, sosa_number, level)
    q = deque()
    q.append((root_id, 1, 0))
    assigned[root_id] = 1

    while q:
        pid, sosa, level = q.popleft()
        # basic entry
        parents_list, nb_families = _parents_of_person(storage, pid)
        # take first parents tuple as canonical for sosa numbering
        father_id, mother_id = parents_list[0]
        has_parents = (father_id is not None or mother_id is not None)
        entry = {
            "person_id": pid,
            "sosa": sosa,
            "level": level,
            "father_sosa": 2 * sosa if father_id else None,
            "mother_sosa": 2 * sosa + 1 if mother_id else None,
            "has_parents": has_parents,
            "nb_families": nb_families,
        }
        result.append(entry)

        if level >= max_depth:
            continue

        # enqueue parents if present and not already assigned
        if father_id:
            if father_id not in assigned:
                assigned[father_id] = 2 * sosa
                q.append((father_id, 2 * sosa, level + 1))
        if mother_id:
            if mother_id not in assigned:
                assigned[mother_id] = 2 * sosa + 1
                q.append((mother_id, 2 * sosa + 1, level + 1))

    # sort results by sosa number
    result.sort(key=lambda x: x["sosa"])  # root first
    return result
