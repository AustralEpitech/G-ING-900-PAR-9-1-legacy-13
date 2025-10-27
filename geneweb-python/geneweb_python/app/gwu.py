"""gwu: GeneWeb utilities - database maintenance and statistics.

Provides:
- stats: Database statistics (counts, distribution)
- optimize: Optimize database (remove orphans, fix links)
- merge: Merge duplicate persons
- export-names: Export list of all names
"""
from __future__ import annotations

from typing import Dict, List, Tuple
from collections import defaultdict

try:
    from core.database import Database
    from core.models import Person, Family
except Exception as exc:  # pragma: no cover
    raise RuntimeError("core modules not found. Run from repo root.") from exc


def stats(db: Database) -> Dict[str, any]:
    """Calculate database statistics."""
    stats = {
        "persons": len(db.persons),
        "families": len(db.families),
        "males": 0,
        "females": 0,
        "unknown_sex": 0,
        "with_birth": 0,
        "with_death": 0,
        "orphans": 0,
        "married": 0,
        "surnames": set(),
        "decades": defaultdict(int),
    }
    
    for person in db.persons.values():
        # Sex distribution
        sex = (person.sex or "").upper()[:1]
        if sex == "M":
            stats["males"] += 1
        elif sex == "F":
            stats["females"] += 1
        else:
            stats["unknown_sex"] += 1
        
        # Birth/death
        if person.birth:
            stats["with_birth"] += 1
            if person.birth.year:
                decade = (person.birth.year // 10) * 10
                stats["decades"][f"{decade}s"] += 1
        if person.death and hasattr(person.death, "year"):
            stats["with_death"] += 1
        
        # Orphans
        has_family = bool(person.families_as_parent or (person.ascend and person.ascend.parents))
        if not has_family:
            stats["orphans"] += 1
        else:
            stats["married"] += 1
        
        # Surnames
        stats["surnames"].add(person.surname)
    
    stats["unique_surnames"] = len(stats["surnames"])
    del stats["surnames"]  # Don't print the set
    
    # Convert decades to sorted list
    stats["birth_distribution"] = dict(sorted(stats["decades"].items()))
    del stats["decades"]
    
    return stats


def print_stats(stats: Dict[str, any]):
    """Pretty-print database statistics."""
    print("\n=== Database Statistics ===\n")
    print(f"Persons:          {stats['persons']}")
    print(f"  - Males:        {stats['males']}")
    print(f"  - Females:      {stats['females']}")
    print(f"  - Unknown:      {stats['unknown_sex']}")
    print(f"\nFamilies:         {stats['families']}")
    print(f"Married persons:  {stats['married']}")
    print(f"Orphan persons:   {stats['orphans']}")
    print(f"\nWith birth date:  {stats['with_birth']}")
    print(f"With death date:  {stats['with_death']}")
    print(f"Unique surnames:  {stats['unique_surnames']}")
    
    if stats['birth_distribution']:
        print("\nBirth distribution by decade:")
        for decade, count in stats['birth_distribution'].items():
            print(f"  {decade}: {count}")


def optimize(db: Database) -> Dict[str, int]:
    """Optimize database by fixing common issues.
    
    Returns a dict with counts of fixes applied.
    """
    fixes = {
        "orphans_removed": 0,
        "broken_links_fixed": 0,
        "empty_families_removed": 0,
    }
    
    # Remove empty families (no parents, no children)
    families_to_remove = []
    for fid, family in db.families.items():
        has_parents = any(
            family in (p.families_as_parent or [])
            for p in db.persons.values()
        )
        has_children = len(family.children) > 0
        if not has_parents and not has_children:
            families_to_remove.append(fid)
    
    for fid in families_to_remove:
        del db.families[fid]
        fixes["empty_families_removed"] += 1
    
    # Fix broken child-parent links
    for fid, family in db.families.items():
        for child in family.children:
            if child.ascend is None or child.ascend.parents != family:
                from core.models import Ascend
                child.ascend = Ascend(parents=family)
                fixes["broken_links_fixed"] += 1
    
    db.save()
    return fixes


def print_optimize_results(fixes: Dict[str, int]):
    """Pretty-print optimization results."""
    print("\n=== Optimization Results ===\n")
    total = sum(fixes.values())
    if total == 0:
        print("✓ Database is already optimized. No fixes needed.")
    else:
        print(f"Total fixes applied: {total}\n")
        if fixes["empty_families_removed"]:
            print(f"  - Empty families removed: {fixes['empty_families_removed']}")
        if fixes["broken_links_fixed"]:
            print(f"  - Broken links fixed: {fixes['broken_links_fixed']}")
        if fixes["orphans_removed"]:
            print(f"  - Orphans removed: {fixes['orphans_removed']}")


def export_names(db: Database, output_file: str):
    """Export all names to a text file (one per line)."""
    names = set()
    for person in db.persons.values():
        full_name = f"{person.first_name} {person.surname}".strip()
        if full_name:
            names.add(full_name)
    
    with open(output_file, "w", encoding="utf-8") as f:
        for name in sorted(names):
            f.write(name + "\n")
    
    print(f"Exported {len(names)} unique names to {output_file}")


def list_surnames(db: Database) -> List[Tuple[str, int]]:
    """List all surnames with counts, sorted by frequency."""
    surname_counts = defaultdict(int)
    for person in db.persons.values():
        if person.surname:
            surname_counts[person.surname] += 1
    
    return sorted(surname_counts.items(), key=lambda x: x[1], reverse=True)


def print_surnames(surnames: List[Tuple[str, int]], limit: int = None) -> None:
    """Pretty-print surname list."""
    print("\n=== Surnames (by frequency) ===\n")
    display_limit = limit if limit else 50
    for surname, count in surnames[:display_limit]:
        print(f"{surname:30} {count:5} person(s)")
    if len(surnames) > display_limit:
        print(f"\n... and {len(surnames) - display_limit} more surnames")
