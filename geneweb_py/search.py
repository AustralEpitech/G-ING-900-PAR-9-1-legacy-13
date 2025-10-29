from __future__ import annotations
from typing import List, Tuple, Optional
from .models import Person, Family
from unicodedata import normalize as _uni_norm


def _normalize_text(s: Optional[str]) -> str:
    if not s:
        return ""
    # remove accents, lowercase
    nf = _uni_norm("NFKD", s)
    ascii_only = "".join([c for c in nf if ord(c) < 128])
    return ascii_only.lower()


def _person_search_fields(p: Person) -> List[Tuple[str, str]]:
    """Return list of (field_name, normalized_text) for searchable person fields."""
    fields = []
    fields.append(("first_name", _normalize_text(p.first_name)))
    fields.append(("surname", _normalize_text(p.surname)))
    full = f"{p.first_name or ''} {p.surname or ''}".strip()
    fields.append(("fullname", _normalize_text(full)))
    if getattr(p, "birth_place", None):
        try:
            fields.append(("birth_place", _normalize_text(p.birth_place.to_simple() or "")))
        except Exception:
            fields.append(("birth_place", ""))
    # notes and events
    if getattr(p, "notes", None):
        fields.append(("notes", _normalize_text(" ".join(p.notes))))
    if getattr(p, "pevents", None):
        ev = " ".join([getattr(e, "kind", "") or "" for e in p.pevents])
        fields.append(("pevents", _normalize_text(ev)))
    return fields


def _family_search_label(f: Family, persons_by_id) -> str:
    # build label from parent surnames (husband then wife), similar to app.families_list
    names = []
    if f.husband_id:
        p = persons_by_id.get(f.husband_id)
        if p:
            names.append(p.surname or "")
    if f.wife_id:
        p = persons_by_id.get(f.wife_id)
        if p:
            names.append(p.surname or "")
    # include child surnames as additional tokens
    for cid in getattr(f, "children_ids", []) or []:
        p = persons_by_id.get(cid)
        if p:
            names.append(p.surname or "")
    lab = " ".join([n for n in names if n])
    return _normalize_text(lab)


def search_people(all_persons: List[Person], q: str, limit: int = 50) -> List[Person]:
    """Search persons by query string q. Returns list of Person ordered by relevance."""
    if not q:
        return []
    qnorm = _normalize_text(q)
    tokens = [t for t in qnorm.split() if t]
    if not tokens:
        return []

    scored = []
    for p in all_persons:
        fields = _person_search_fields(p)
        score = 0
        matched_all = True
        for tok in tokens:
            tok_matched = False
            best_field_score = 0
            for fname, txt in fields:
                if not txt:
                    continue
                if txt == tok:
                    s = 100
                elif txt.split() and tok in txt.split():
                    s = 70
                elif txt.startswith(tok):
                    s = 50
                elif tok in txt:
                    s = 20
                else:
                    s = 0
                # boost matches in surname/firstname/fullname
                if s and fname == "surname":
                    s += 30
                if s and fname == "first_name":
                    s += 20
                if s and fname == "fullname":
                    s += 10
                if s > best_field_score:
                    best_field_score = s
                if s:
                    tok_matched = True
            if not tok_matched:
                matched_all = False
                break
            score += best_field_score
        if matched_all and score > 0:
            scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:limit]]


def search_families(all_families: List[Family], all_persons: List[Person], q: str, limit: int = 50) -> List[Family]:
    if not q:
        return []
    persons_by_id = {p.id: p for p in all_persons}
    qnorm = _normalize_text(q)
    tokens = [t for t in qnorm.split() if t]
    if not tokens:
        return []
    scored = []
    for f in all_families:
        label = _family_search_label(f, persons_by_id)
        score = 0
        matched_all = True
        for tok in tokens:
            if not label:
                matched_all = False
                break
            if label == tok:
                s = 200
            elif tok in label.split():
                s = 100
            elif label.startswith(tok):
                s = 60
            elif tok in label:
                s = 20
            else:
                matched_all = False
                break
            score += s
        if matched_all and score > 0:
            scored.append((score, f))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [f for _, f in scored[:limit]]
