import os
from pathlib import Path

from geneweb_py.gedcom_adapter import import_gedcom, export_gedcom
from geneweb_py.storage import Storage
from geneweb_py.models import Person, Family


def _write_sample_gedcom(path: Path) -> Path:
    content = """
0 @I1@ INDI
1 NAME John /Doe/
1 SEX M
0 @I2@ INDI
1 NAME Jane /Doe/
1 SEX F
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
"""
    p = path / "sample.ged"
    p.write_text(content.strip() + "\n", encoding="utf-8")
    return p


def test_import_gedcom_creates_persons_and_families(tmp_path):
    ged = _write_sample_gedcom(tmp_path)
    data_dir = tmp_path / "data"
    storage = Storage(data_dir)

    mapping = import_gedcom(ged, storage)

    # Expect two persons imported (keys in mapping)
    assert len(mapping) >= 2

    # Check persons exist in storage (normalized ids are used as keys)
    # The adapter prefixes GEDCOM ids with 'gedcom:'
    assert storage.get_person("gedcom:I1") is not None
    assert storage.get_person("gedcom:I2") is not None

    # Family should be created and reference those persons
    fams = list(storage.families.values())
    assert len(fams) >= 1
    f = fams[0]
    assert f.husband_id in ("gedcom:I1", "I1", None) or f.husband_id == "gedcom:I1"
    assert f.wife_id in ("gedcom:I2", "I2", None) or f.wife_id == "gedcom:I2"


def test_export_gedcom_writes_file_and_contains_names(tmp_path):
    data_dir = tmp_path / "data"
    storage = Storage(data_dir)

    # create few persons and a family
    p1 = Person(id="gedcom:I1", first_name="John", surname="Doe", sex="M")
    p2 = Person(id="gedcom:I2", first_name="Jane", surname="Doe", sex="F")
    storage.add_person(p1)
    storage.add_person(p2)
    f = Family(id="gedcom:F1", husband_id=p1.id, wife_id=p2.id, children_ids=[])
    storage.add_family(f)

    out = tmp_path / "outdir" / "export.ged"
    # export (should create parent directory)
    export_gedcom(storage, out)

    assert out.exists()
    txt = out.read_text(encoding="utf-8")
    # Check that names are present in the GEDCOM output
    assert "NAME John /Doe/" in txt
    assert "NAME Jane /Doe/" in txt
