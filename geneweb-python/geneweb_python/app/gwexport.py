"""gwexport: Export GeneWeb database to multiple formats.

Provides:
- csv: Export to CSV files (persons.csv, families.csv)
- json: Export to JSON (full database dump)
- html: Export to HTML (basic family tree view)
"""
from __future__ import annotations

import csv
import json
from typing import Dict, List
from pathlib import Path

try:
    from core.database import Database
    from core.models import Person, Family, CDate
except Exception as exc:  # pragma: no cover
    raise RuntimeError("core modules not found. Run from repo root.") from exc


def export_csv(db: Database, output_dir: str = "."):
    """Export database to CSV files (persons.csv and families.csv)."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    persons_file = output_path / "persons.csv"
    families_file = output_path / "families.csv"
    
    # Export persons
    with open(persons_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ID", "First Name", "Surname", "Sex", "Birth Date", "Birth Place",
            "Death Date", "Death Place", "Occupation", "Notes"
        ])
        
        for pid, person in db.persons.items():
            birth_date = _format_date(person.birth) if person.birth else ""
            death_date = _format_date(person.death) if hasattr(person.death, "year") else str(person.death or "")
            
            writer.writerow([
                pid,
                person.first_name or "",
                person.surname or "",
                person.sex or "",
                birth_date,
                person.birth_place or "",
                death_date,
                person.death_place or "",
                person.occupation or "",
                person.notes or "",
            ])
    
    # Export families
    with open(families_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ID", "Marriage Date", "Marriage Place", "Divorce", "Comment"
        ])
        
        for fid, family in db.families.items():
            marriage_date = _format_date(family.marriage) if family.marriage else ""
            
            writer.writerow([
                fid,
                marriage_date,
                family.marriage_place or "",
                family.divorce or "",
                family.comment or "",
            ])
    
    print(f"Exported {len(db.persons)} persons to {persons_file}")
    print(f"Exported {len(db.families)} families to {families_file}")


def export_json(db: Database, output_file: str = "database.json"):
    """Export database to JSON format."""
    data = {
        "persons": {},
        "families": {},
        "metadata": {
            "total_persons": len(db.persons),
            "total_families": len(db.families),
        }
    }
    
    # Export persons
    for pid, person in db.persons.items():
        data["persons"][str(pid)] = {
            "id": pid,
            "first_name": person.first_name,
            "surname": person.surname,
            "sex": person.sex,
            "birth": {
                "date": _format_date(person.birth) if person.birth else None,
                "place": person.birth_place or None,
            },
            "death": {
                "date": _format_date(person.death) if hasattr(person.death, "year") else str(person.death) if person.death else None,
                "place": person.death_place or None,
            },
            "occupation": person.occupation or None,
            "notes": person.notes or None,
        }
    
    # Export families
    for fid, family in db.families.items():
        data["families"][str(fid)] = {
            "id": fid,
            "marriage": {
                "date": _format_date(family.marriage) if family.marriage else None,
                "place": family.marriage_place or None,
            },
            "divorce": family.divorce or None,
            "comment": family.comment or None,
        }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Exported database to {output_file}")
    print(f"  - {data['metadata']['total_persons']} persons")
    print(f"  - {data['metadata']['total_families']} families")


def export_html(db: Database, output_file: str = "family_tree.html"):
    """Export database to HTML format (basic family tree view)."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GeneWeb Family Tree</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .stats {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .stats h2 {{
            margin-top: 0;
            color: #4CAF50;
        }}
        .person-list, .family-list {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .person-card, .family-card {{
            border: 1px solid #ddd;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            background-color: #fafafa;
        }}
        .person-card:hover, .family-card:hover {{
            background-color: #e8f5e9;
        }}
        .person-name {{
            font-weight: bold;
            font-size: 1.2em;
            color: #2c3e50;
        }}
        .person-details, .family-details {{
            margin-top: 10px;
            color: #555;
        }}
        .label {{
            font-weight: bold;
            color: #777;
        }}
        .sex-male {{ color: #2196F3; }}
        .sex-female {{ color: #E91E63; }}
    </style>
</head>
<body>
    <h1>🌳 GeneWeb Family Tree</h1>
    
    <div class="stats">
        <h2>Database Statistics</h2>
        <p><strong>Total Persons:</strong> {total_persons}</p>
        <p><strong>Total Families:</strong> {total_families}</p>
    </div>
    
    <div class="person-list">
        <h2>Persons</h2>
        {persons_html}
    </div>
    
    <div class="family-list">
        <h2>Families</h2>
        {families_html}
    </div>
</body>
</html>
"""
    
    # Generate persons HTML
    persons_html = []
    for pid, person in db.persons.items():
        sex_class = "sex-male" if person.sex and person.sex.upper()[0] == "M" else "sex-female" if person.sex and person.sex.upper()[0] == "F" else ""
        full_name = f"{person.first_name} {person.surname}".strip()
        
        birth_info = ""
        if person.birth:
            birth_date = _format_date(person.birth)
            birth_place = person.birth_place or ""
            birth_info = f"{birth_date}" + (f" in {birth_place}" if birth_place else "")
        
        death_info = ""
        if person.death:
            death_date = _format_date(person.death) if hasattr(person.death, "year") else str(person.death)
            death_place = person.death_place or ""
            death_info = f"{death_date}" + (f" in {death_place}" if death_place else "")
        
        person_html = f"""
        <div class="person-card">
            <div class="person-name {sex_class}">
                {full_name} {f"({person.sex})" if person.sex else ""}
            </div>
            <div class="person-details">
                {f'<p><span class="label">Born:</span> {birth_info}</p>' if birth_info else ''}
                {f'<p><span class="label">Died:</span> {death_info}</p>' if death_info else ''}
                {f'<p><span class="label">Occupation:</span> {person.occupation}</p>' if person.occupation else ''}
            </div>
        </div>
        """
        persons_html.append(person_html)
    
    # Generate families HTML
    families_html = []
    for fid, family in db.families.items():
        marriage_info = ""
        if family.marriage:
            marriage_date = _format_date(family.marriage)
            marriage_place = family.marriage_place or ""
            marriage_info = f"{marriage_date}" + (f" in {marriage_place}" if marriage_place else "")
        
        family_html = f"""
        <div class="family-card">
            <div class="person-name">Family #{fid}</div>
            <div class="family-details">
                {f'<p><span class="label">Marriage:</span> {marriage_info}</p>' if marriage_info else ''}
                {f'<p><span class="label">Divorce:</span> {family.divorce}</p>' if family.divorce else ''}
                {f'<p><span class="label">Comment:</span> {family.comment}</p>' if family.comment else ''}
            </div>
        </div>
        """
        families_html.append(family_html)
    
    # Fill template
    html = html.format(
        total_persons=len(db.persons),
        total_families=len(db.families),
        persons_html="\n".join(persons_html) if persons_html else "<p>No persons in database.</p>",
        families_html="\n".join(families_html) if families_html else "<p>No families in database.</p>",
    )
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"Exported HTML family tree to {output_file}")


def _format_date(date) -> str:
    """Format a CDate or date string for display."""
    if not date:
        return ""
    
    if hasattr(date, "year"):
        # It's a CDate object
        parts = []
        if date.precision:
            parts.append(date.precision)
        if date.day:
            parts.append(f"{date.day:02d}")
        if date.month:
            parts.append(f"{date.month:02d}")
        if date.year:
            parts.append(str(date.year))
        return " ".join(parts) if parts else ""
    
    return str(date)
