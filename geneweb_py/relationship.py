"""Relationship graph traversal utilities.

Provides shortest path and all-shortest-paths between two persons in the
family graph. Edges considered: parent <-> child and spouse <-> spouse
(husband<->wife). All edges have weight 1.

API:
    shortest_path(storage, a_id, b_id, max_depth=None) -> (distance, path)
    all_shortest_paths(storage, a_id, b_id, max_paths=100, max_depth=None) -> List[path]

Paths are lists of person ids from source to target (inclusive). If no path is
found, shortest_path returns (None, []) and all_shortest_paths returns [].
"""
from __future__ import annotations
from collections import deque, defaultdict
from typing import List, Dict, Set, Tuple, Optional


def _neighbors(storage, pid: str) -> Set[str]:
    """Return set of neighboring person ids (parents, children, spouses)."""
    nbors: Set[str] = set()
    try:
        fams = list(storage.families_of_person(pid))
    except Exception:
        fams = []
    for fam in fams:
        # parents: if pid is a child in this family, add husband and wife
        if pid in getattr(fam, "children_ids", []):
            if fam.husband_id:
                nbors.add(fam.husband_id)
            if fam.wife_id:
                nbors.add(fam.wife_id)
        # spouses and children
        if fam.husband_id == pid:
            if fam.wife_id:
                nbors.add(fam.wife_id)
            for c in getattr(fam, "children_ids", []):
                nbors.add(c)
        if fam.wife_id == pid:
            if fam.husband_id:
                nbors.add(fam.husband_id)
            for c in getattr(fam, "children_ids", []):
                nbors.add(c)
    # ensure we don't return self
    nbors.discard(pid)
    return nbors


def shortest_path(storage, a_id: str, b_id: str, max_depth: Optional[int] = None) -> Tuple[Optional[int], List[str]]:
    """Return (distance, path) for one shortest path from a_id to b_id.

    Uses a bidirectional BFS for performance. If no path exists, returns
    (None, []). If a_id == b_id returns (0, [a_id]).
    """
    # Validate inputs quickly
    if a_id is None or b_id is None:
        return None, []
    if a_id == b_id:
        return 0, [a_id]
    if a_id not in storage.persons or b_id not in storage.persons:
        return None, []

    # Bidirectional BFS for efficiency on large graphs
    forward_front = {a_id}
    backward_front = {b_id}

    # parent pointers for path reconstruction: node -> predecessor
    fprev: Dict[str, Optional[str]] = {a_id: None}
    bprev: Dict[str, Optional[str]] = {b_id: None}

    # depth maps
    fdepth: Dict[str, int] = {a_id: 0}
    bdepth: Dict[str, int] = {b_id: 0}

    # neighbor cache to avoid repeated storage lookups
    neigh_cache: Dict[str, Set[str]] = {}

    def get_neighbors(node: str) -> Set[str]:
        if node in neigh_cache:
            return neigh_cache[node]
        n = _neighbors(storage, node)
        neigh_cache[node] = n
        return n

    max_combined = max_depth if max_depth is not None else None

    # Expand alternately from the smaller frontier
    while forward_front and backward_front:
        # choose the smaller frontier to expand
        if len(forward_front) <= len(backward_front):
            expanding_forward = True
            current_front = forward_front
        else:
            expanding_forward = False
            current_front = backward_front

        next_front: Set[str] = set()
        for cur in current_front:
            cur_depth = fdepth[cur] if expanding_forward else bdepth[cur]
            # respect max_depth constraint
            if max_combined is not None and cur_depth >= max_combined:
                continue
            for nb in get_neighbors(cur):
                # check if neighbor already discovered on this side
                if expanding_forward:
                    if nb in fprev:
                        continue
                    fprev[nb] = cur
                    fdepth[nb] = cur_depth + 1
                else:
                    if nb in bprev:
                        continue
                    bprev[nb] = cur
                    bdepth[nb] = cur_depth + 1

                # meeting test: neighbor discovered by the other side?
                if (expanding_forward and nb in bprev) or (not expanding_forward and nb in fprev):
                    meet = nb
                    dist = fdepth.get(meet, 0) + bdepth.get(meet, 0)
                    if max_combined is not None and dist > max_combined:
                        return None, []
                    # reconstruct forward path a -> meet
                    path_f: List[str] = []
                    node = meet
                    while node is not None:
                        path_f.append(node)
                        node = fprev.get(node)
                    path_f.reverse()
                    # reconstruct backward path from meet -> b (excluding meet)
                    path_b: List[str] = []
                    node = bprev.get(meet)
                    while node is not None:
                        path_b.append(node)
                        node = bprev.get(node)
                    full_path = path_f + path_b
                    return dist, full_path

                next_front.add(nb)

        if expanding_forward:
            forward_front = next_front
        else:
            backward_front = next_front

    return None, []


def all_shortest_paths(storage, a_id: str, b_id: str, max_paths: int = 100, max_depth: Optional[int] = None) -> List[List[str]]:
    """Return all shortest paths (up to max_paths) between a_id and b_id.

    We perform a BFS that records predecessors for nodes at the shortest
    distance. Once the target is reached at level L we stop exploring deeper
    levels and backtrack to enumerate all shortest paths.
    """
    if a_id is None or b_id is None:
        return []
    if a_id == b_id:
        return [[a_id]]
    if a_id not in storage.persons or b_id not in storage.persons:
        return []

    # BFS with level tracking and predecessors
    levels: Dict[str, int] = {a_id: 0}
    preds: Dict[str, Set[str]] = defaultdict(set)

    q = deque([a_id])
    found_level: Optional[int] = None

    while q:
        cur = q.popleft()
        cur_level = levels[cur]
        if found_level is not None and cur_level >= found_level:
            # we've reached or passed the level where target was found; skip
            continue
        if max_depth is not None and cur_level >= max_depth:
            continue
        for nb in _neighbors(storage, cur):
            if nb not in levels:
                levels[nb] = cur_level + 1
                preds[nb].add(cur)
                if nb == b_id:
                    found_level = cur_level + 1
                else:
                    q.append(nb)
            else:
                # if we encounter nb again at same shortest level, add predecessor
                if levels[nb] == cur_level + 1:
                    preds[nb].add(cur)
    if b_id not in preds:
        return []

    # backtrack from b_id to a_id using preds to enumerate paths
    paths: List[List[str]] = []

    def backtrack(node: str, acc: List[str]):
        if len(paths) >= max_paths:
            return
        if node == a_id:
            paths.append(list(reversed(acc + [a_id])))
            return
        for p in preds.get(node, []):
            backtrack(p, acc + [node])

    backtrack(b_id, [])
    return paths
