"""check: Data validation and consistency checks for genealogical database.

Inspired by GeneWeb's check/fixbase modules, this validates:
- Orphan persons (not in any family)
- Missing parents/children references
- Duplicate names
- Invalid dates (death before birth, etc.)
"""
from __future__ import annotations

from typing import List, Dict, Tuple, Optional

try:
    from core.database import Database
    from core.models import Person, Family, CDate
except Exception as exc:  # pragma: no cover
    raise RuntimeError("core modules not found. Run from repo root.") from exc


class CheckIssue:
    """Represents a data consistency issue."""

    def __init__(self, severity: str, category: str, message: str, person_id: Optional[int] = None, family_id: Optional[int] = None):
        self.severity = severity  # "error", "warning", "info"
        self.category = category  # "orphan", "date", "duplicate", etc.
        self.message = message
        self.person_id = person_id
        self.family_id = family_id

    def __repr__(self):
        loc = ""
        if self.person_id is not None:
            loc = f" [Person {self.person_id}]"
        elif self.family_id is not None:
            loc = f" [Family {self.family_id}]"
        return f"[{self.severity.upper()}] {self.category}: {self.message}{loc}"


def check_database(db: Database) -> List[CheckIssue]:
    """Run all consistency checks on the database and return a list of issues."""
    issues = []
    issues.extend(_check_orphan_persons(db))
    issues.extend(_check_date_consistency(db))
    issues.extend(_check_duplicate_names(db))
    issues.extend(_check_family_links(db))
    return issues


def _check_orphan_persons(db: Database) -> List[CheckIssue]:
    """Find persons not linked to any family (as parent or child)."""
    issues = []
    for pid, person in db.persons.items():
        has_family = False
        if person.families_as_parent:
            has_family = True
        if person.ascend and person.ascend.parents:
            has_family = True
        if not has_family:
            issues.append(CheckIssue(
                severity="info",
                category="orphan",
                message=f"{person.first_name} {person.surname} is not linked to any family",
                person_id=pid
            ))
    return issues


def _check_date_consistency(db: Database) -> List[CheckIssue]:
    """Check for invalid dates (e.g., death before birth)."""
    issues = []
    for pid, person in db.persons.items():
        birth = person.birth
        death = person.death
        if birth and death and hasattr(death, "year"):
            if birth.year and death.year and death.year < birth.year:
                issues.append(CheckIssue(
                    severity="error",
                    category="date",
                    message=f"{person.first_name} {person.surname} died before birth ({death.year} < {birth.year})",
                    person_id=pid
                ))
    return issues


def _check_duplicate_names(db: Database) -> List[CheckIssue]:
    """Find persons with duplicate names (same first_name and surname)."""
    issues = []
    name_map: Dict[Tuple[str, str], List[int]] = {}
    for pid, person in db.persons.items():
        key = (person.first_name.lower(), person.surname.lower())
        if key not in name_map:
            name_map[key] = []
        name_map[key].append(pid)

    for (first, last), pids in name_map.items():
        if len(pids) > 1:
            issues.append(CheckIssue(
                severity="warning",
                category="duplicate",
                message=f"Duplicate name: {first.title()} {last.title()} ({len(pids)} persons: {pids})"
            ))
    return issues


def _check_family_links(db: Database) -> List[CheckIssue]:
    """Check for broken family links (e.g., child in family.children but ascend.parents doesn't match)."""
    issues = []
    for fid, family in db.families.items():
        for child in family.children:
            if child.ascend is None or child.ascend.parents != family:
                # Find child ID
                child_id = None
                for pid, p in db.persons.items():
                    if p == child:
                        child_id = pid
                        break
                issues.append(CheckIssue(
                    severity="warning",
                    category="link",
                    message=f"Child in family {fid} but ascend.parents doesn't match",
                    person_id=child_id,
                    family_id=fid
                ))
    return issues


def print_issues(issues: List[CheckIssue]):
    """Pretty-print issues grouped by severity."""
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    infos = [i for i in issues if i.severity == "info"]

    if errors:
        print(f"\n{len(errors)} ERROR(S):")
        for issue in errors:
            print(f"  {issue}")
    if warnings:
        print(f"\n{len(warnings)} WARNING(S):")
        for issue in warnings:
            print(f"  {issue}")
    if infos:
        print(f"\n{len(infos)} INFO:")
        for issue in infos:
            print(f"  {issue}")

    if not issues:
        print("✓ No issues found. Database looks good!")
