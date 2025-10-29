"""Cousin / kinship label helpers.

APIs:
    cousin_label(l1, l2) -> (label, degree, removed)

Inputs l1 and l2 are generation distances from each person to their most
recent common ancestor (MRCA). For example:
    - parent <-> child : l1=0, l2=1
    - siblings: l1=1, l2=1
    - first cousins: l1=2, l2=2
    - aunt/niece: l1=1, l2=2 (first is aunt/uncle relative to second)

The returned tuple contains a human-friendly label (relative to the first
person), and when applicable the cousin degree and removals.
"""
from typing import Optional, Tuple


def _ordinal(n: int) -> str:
    if 10 <= (n % 100) <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def cousin_label(l1: int, l2: int) -> Tuple[str, Optional[int], Optional[int]]:
    """Return (label, degree, removed) for distances l1,l2 to the MRCA.

    label is a short human-friendly descriptor relative to the first person.
    degree and removed are meaningful for 'cousin' relations (degree >=1).
    For ancestor/descendant cases (one distance == 0) the label describes
    the relationship of person1 relative to person2 (e.g. 'parent',
    'grandparent', 'child', 'grandchild').
    """
    # Validate inputs
    if l1 < 0 or l2 < 0:
        raise ValueError("l1 and l2 must be non-negative integers")

    # same person
    if l1 == 0 and l2 == 0:
        return "self", None, None

    # ancestor / descendant special cases
    if l1 == 0 or l2 == 0:
        # person1 is ancestor of person2 if l1==0
        if l1 == 0 and l2 == 1:
            return "parent", None, None
        if l1 == 0 and l2 == 2:
            return "grandparent", None, None
        if l1 == 1 and l2 == 0:
            return "child", None, None
        if l1 == 2 and l2 == 0:
            return "grandchild", None, None
        # more distant ancestor/descendant
        if l1 == 0 and l2 > 2:
            return (f"ancestor (gen {l2})", None, None)
        if l2 == 0 and l1 > 2:
            return (f"descendant (gen {l1})", None, None)

    # both at least 1 generation to MRCA -> cousin-family
    # degree = min(l1, l2) - 1, removals = abs(l1 - l2)
    degree = min(l1, l2) - 1
    removed = abs(l1 - l2)

    if degree == 0:
        # degree 0 with removed 0 => siblings
        if removed == 0:
            return "sibling", 0, 0
        # degree 0 with removed >0 => aunt/uncle vs niece/nephew
        # relative to person1: if l1 < l2 then person1 is aunt/uncle
        if l1 < l2:
            return "aunt/uncle", 0, removed
        else:
            return "niece/nephew", 0, removed

    # general cousin cases
    # e.g., degree=1 -> '1st cousin'
    ord_deg = _ordinal(degree)
    if removed == 0:
        label = f"{ord_deg} cousin"
    elif removed == 1:
        label = f"{ord_deg} cousin once removed"
    else:
        label = f"{ord_deg} cousin {removed} times removed"

    return label, degree, removed
