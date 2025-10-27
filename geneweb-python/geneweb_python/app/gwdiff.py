"""gwdiff: Compare two GeneWeb databases and show differences.

Provides:
- diff: Compare two database files and show differences
"""
from __future__ import annotations

from typing import Dict, List, Tuple, Set
import json

try:
    from core.database import Database
    from core.models import Person, Family
except Exception as exc:  # pragma: no cover
    raise RuntimeError("core modules not found. Run from repo root.") from exc


def compare_databases(db1: Database, db2: Database) -> Dict[str, any]:
    """Compare two databases and return a report of differences.
    
    Args:
        db1: First database (baseline)
        db2: Second database (comparison target)
    
    Returns:
        Dictionary with:
        - persons_added: List of person IDs added in db2
        - persons_removed: List of person IDs removed from db1
        - persons_modified: List of (person_id, changes) tuples
        - families_added: List of family IDs added in db2
        - families_removed: List of family IDs removed from db1
        - families_modified: List of (family_id, changes) tuples
    """
    report = {
        "persons_added": [],
        "persons_removed": [],
        "persons_modified": [],
        "families_added": [],
        "families_removed": [],
        "families_modified": [],
    }
    
    # Compare persons
    db1_person_ids = set(db1.persons.keys())
    db2_person_ids = set(db2.persons.keys())
    
    report["persons_added"] = list(db2_person_ids - db1_person_ids)
    report["persons_removed"] = list(db1_person_ids - db2_person_ids)
    
    # Check for modifications in common persons
    common_person_ids = db1_person_ids & db2_person_ids
    for pid in common_person_ids:
        p1 = db1.persons[pid]
        p2 = db2.persons[pid]
        changes = _compare_persons(p1, p2)
        if changes:
            report["persons_modified"].append((pid, changes))
    
    # Compare families
    db1_family_ids = set(db1.families.keys())
    db2_family_ids = set(db2.families.keys())
    
    report["families_added"] = list(db2_family_ids - db1_family_ids)
    report["families_removed"] = list(db1_family_ids - db2_family_ids)
    
    # Check for modifications in common families
    common_family_ids = db1_family_ids & db2_family_ids
    for fid in common_family_ids:
        f1 = db1.families[fid]
        f2 = db2.families[fid]
        changes = _compare_families(f1, f2)
        if changes:
            report["families_modified"].append((fid, changes))
    
    return report


def _compare_persons(p1: Person, p2: Person) -> Dict[str, Tuple[any, any]]:
    """Compare two Person objects and return differences.
    
    Returns:
        Dict mapping field name to (old_value, new_value) tuples
    """
    changes = {}
    
    # Compare basic fields
    fields = [
        "first_name", "surname", "sex", "birth_place", "death_place",
        "occupation", "public_name", "image", "notes", "access"
    ]
    
    for field in fields:
        v1 = getattr(p1, field, None)
        v2 = getattr(p2, field, None)
        if v1 != v2:
            changes[field] = (v1, v2)
    
    # Compare birth/death dates
    birth1 = _serialize_date(p1.birth) if p1.birth else None
    birth2 = _serialize_date(p2.birth) if p2.birth else None
    if birth1 != birth2:
        changes["birth"] = (birth1, birth2)
    
    death1 = _serialize_date(p1.death) if hasattr(p1.death, "year") else str(p1.death) if p1.death else None
    death2 = _serialize_date(p2.death) if hasattr(p2.death, "year") else str(p2.death) if p2.death else None
    if death1 != death2:
        changes["death"] = (death1, death2)
    
    return changes


def _compare_families(f1: Family, f2: Family) -> Dict[str, Tuple[any, any]]:
    """Compare two Family objects and return differences.
    
    Returns:
        Dict mapping field name to (old_value, new_value) tuples
    """
    changes = {}
    
    # Compare basic fields
    fields = [
        "marriage_place", "marriage_note", "relation", "divorce", "comment"
    ]
    
    for field in fields:
        v1 = getattr(f1, field, None)
        v2 = getattr(f2, field, None)
        if v1 != v2:
            changes[field] = (v1, v2)
    
    # Compare marriage date
    marriage1 = _serialize_date(f1.marriage) if f1.marriage else None
    marriage2 = _serialize_date(f2.marriage) if f2.marriage else None
    if marriage1 != marriage2:
        changes["marriage"] = (marriage1, marriage2)
    
    return changes


def _serialize_date(date) -> str:
    """Serialize a CDate to a string for comparison."""
    if not date:
        return None
    if hasattr(date, "year"):
        parts = []
        if date.precision:
            parts.append(date.precision)
        if date.day:
            parts.append(f"{date.day:02d}")
        if date.month:
            parts.append(f"{date.month:02d}")
        if date.year:
            parts.append(str(date.year))
        return " ".join(parts) if parts else None
    return str(date)


def print_diff_report(report: Dict[str, any], db1_path: str, db2_path: str):
    """Pretty-print the diff report."""
    print(f"\n=== Database Comparison ===")
    print(f"Baseline: {db1_path}")
    print(f"Target:   {db2_path}\n")
    
    total_changes = (
        len(report["persons_added"]) +
        len(report["persons_removed"]) +
        len(report["persons_modified"]) +
        len(report["families_added"]) +
        len(report["families_removed"]) +
        len(report["families_modified"])
    )
    
    if total_changes == 0:
        print("✓ Databases are identical. No differences found.")
        return
    
    print(f"Total changes: {total_changes}\n")
    
    # Persons
    if report["persons_added"]:
        print(f"Persons added ({len(report['persons_added'])}):")
        for pid in report["persons_added"][:10]:  # Show first 10
            print(f"  + Person ID {pid}")
        if len(report["persons_added"]) > 10:
            print(f"  ... and {len(report['persons_added']) - 10} more")
        print()
    
    if report["persons_removed"]:
        print(f"Persons removed ({len(report['persons_removed'])}):")
        for pid in report["persons_removed"][:10]:  # Show first 10
            print(f"  - Person ID {pid}")
        if len(report["persons_removed"]) > 10:
            print(f"  ... and {len(report['persons_removed']) - 10} more")
        print()
    
    if report["persons_modified"]:
        print(f"Persons modified ({len(report['persons_modified'])}):")
        for pid, changes in report["persons_modified"][:5]:  # Show first 5 with details
            print(f"  ~ Person ID {pid}:")
            for field, (old, new) in changes.items():
                print(f"      {field}: '{old}' → '{new}'")
        if len(report["persons_modified"]) > 5:
            print(f"  ... and {len(report['persons_modified']) - 5} more")
        print()
    
    # Families
    if report["families_added"]:
        print(f"Families added ({len(report['families_added'])}):")
        for fid in report["families_added"][:10]:  # Show first 10
            print(f"  + Family ID {fid}")
        if len(report["families_added"]) > 10:
            print(f"  ... and {len(report['families_added']) - 10} more")
        print()
    
    if report["families_removed"]:
        print(f"Families removed ({len(report['families_removed'])}):")
        for fid in report["families_removed"][:10]:  # Show first 10
            print(f"  - Family ID {fid}")
        if len(report["families_removed"]) > 10:
            print(f"  ... and {len(report['families_removed']) - 10} more")
        print()
    
    if report["families_modified"]:
        print(f"Families modified ({len(report['families_modified'])}):")
        for fid, changes in report["families_modified"][:5]:  # Show first 5 with details
            print(f"  ~ Family ID {fid}:")
            for field, (old, new) in changes.items():
                print(f"      {field}: '{old}' → '{new}'")
        if len(report["families_modified"]) > 5:
            print(f"  ... and {len(report['families_modified']) - 5} more")
        print()


def export_diff_json(report: Dict[str, any], output_file: str):
    """Export the diff report as JSON."""
    # Convert tuples to lists for JSON serialization
    serializable_report = {
        "persons_added": report["persons_added"],
        "persons_removed": report["persons_removed"],
        "persons_modified": [
            {"id": pid, "changes": {k: {"old": v[0], "new": v[1]} for k, v in changes.items()}}
            for pid, changes in report["persons_modified"]
        ],
        "families_added": report["families_added"],
        "families_removed": report["families_removed"],
        "families_modified": [
            {"id": fid, "changes": {k: {"old": v[0], "new": v[1]} for k, v in changes.items()}}
            for fid, changes in report["families_modified"]
        ],
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(serializable_report, f, indent=2, ensure_ascii=False)
    
    print(f"Exported diff report to {output_file}")
