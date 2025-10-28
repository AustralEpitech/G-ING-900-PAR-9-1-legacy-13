"""Command-line GEDCOM importer/exporter for geneweb-py.

Usage examples:

python scripts/import_gedcom.py import --file path/to/file.ged --data-dir data
python scripts/import_gedcom.py export --out path/to/out.ged --data-dir data

"""
from pathlib import Path
import argparse
import sys

# ensure package importable when running from repo root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from geneweb_py.storage import Storage
from geneweb_py.gedcom_adapter import import_gedcom, export_gedcom


def main(argv=None):
    p = argparse.ArgumentParser(prog="import_gedcom")
    sub = p.add_subparsers(dest="cmd", required=True)
    imp = sub.add_parser("import")
    imp.add_argument("--file", "-f", required=True, help="Path to GEDCOM file to import")
    imp.add_argument("--data-dir", default="data", help="Data dir (where storage.db lives or will be created)")
    exp = sub.add_parser("export")
    exp.add_argument("--out", "-o", required=True, help="Output GEDCOM path")
    exp.add_argument("--data-dir", default="data", help="Data dir (where storage.db lives)")

    args = p.parse_args(argv)

    data_dir = Path(args.data_dir)
    storage = Storage(data_dir)

    if args.cmd == "import":
        ged = Path(args.file)
        if not ged.exists():
            print(f"GEDCOM file not found: {ged}")
            return 2
        mapping = import_gedcom(ged, storage)
        print(f"Imported GEDCOM; created/mapped {len(mapping)} persons")
        return 0
    elif args.cmd == "export":
        out = Path(args.out)
        export_gedcom(storage, out)
        print(f"Exported GEDCOM to {out}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
