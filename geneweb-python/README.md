# geneweb-python

A comprehensive Python reimplementation of the GeneWeb OCaml genealogy software.

This package provides a complete set of tools for managing genealogical databases, including import/export, data validation, web API, utilities, and interactive console.

## 🎯 Status

**Phase 2 Complete**: All core commands implemented with comprehensive test coverage (23 tests passing).

See [PORTING_STATUS.md](PORTING_STATUS.md) for detailed progress tracking.

## ✨ Features

### 🗂️ Core Commands (8/8 implemented)

1. **gwb2ged** - Export to GEDCOM format with family links
2. **ged2gwb** - Import from GEDCOM format with bidirectional support
3. **gwd** - HTTP REST API daemon for web queries
4. **check** - Data validation and consistency checks
5. **gwu** - Database utilities (stats, optimize, export-names, list-surnames)
6. **gwdiff** - Compare two databases and show differences
7. **gwexport** - Multi-format export (CSV, JSON, HTML)
8. **gwc** - Interactive console with command history

### 📊 Test Coverage

- **23 passing tests** covering all features
- Bidirectional GEDCOM roundtrip tests
- HTTP API integration tests
- Data validation tests
- Multi-format export tests

## 🚀 Quick Start

### Installation

```bash
# From repo root
cd geneweb-python
python -m pip install -e .
```

### Using the wrapper script (recommended)

```bash
# From repo root
python geneweb-cli.py --help
```

## 📖 Commands

### gwb2ged (GEDCOM Export)

Export database to GEDCOM format with full family linkage:

```bash
python geneweb-cli.py gwb2ged --db-file database.pkl -o output.ged
```

Features:
- HEAD/INDI/FAM/TRLR tags
- HUSB/WIFE/CHIL family links
- FAMS/FAMC bidirectional references
- Full date and place support

### ged2gwb (GEDCOM Import)

Import GEDCOM files into database:

```bash
python geneweb-cli.py ged2gwb input.ged --db-file database.pkl
```

Features:
- Two-pass parsing for complete family linkage
- Supports INDI and FAM records
- Preserves dates, places, and relationships
- Bidirectional roundtrip compatibility

### gwd (HTTP REST API)

Start web server for database queries:

```bash
python geneweb-cli.py gwd --db-file database.pkl --host 127.0.0.1 --port 2317
```

Endpoints:
- `GET /persons` - List all persons (filter: `?surname=<name>`)
- `GET /persons/<id>` - Get person by ID
- `GET /families` - List all families  
- `GET /families/<id>` - Get family by ID
- `GET /search?q=<query>` - Search persons by name

Example:
```bash
curl http://127.0.0.1:2317/persons
curl http://127.0.0.1:2317/search?q=Smith
```

### check (Data Validation)

Validate database consistency:

```bash
python geneweb-cli.py check --db-file database.pkl
```

Checks:
- Orphan persons (not linked to any family)
- Invalid dates (death before birth)
- Duplicate names
- Broken family links

### gwu (Database Utilities)

#### Statistics

```bash
python geneweb-cli.py gwu stats --db-file database.pkl
```

Shows: person count, sex distribution, birth/death counts, unique surnames, birth distribution by decade

#### Optimize

```bash
python geneweb-cli.py gwu optimize --db-file database.pkl
```

Fixes: empty families, broken child-parent links

#### Export Names

```bash
python geneweb-cli.py gwu export-names --db-file database.pkl -o names.txt
```

#### List Surnames

```bash
python geneweb-cli.py gwu list-surnames --db-file database.pkl --limit 20
```

### gwdiff (Database Comparison)

Compare two databases:

```bash
python geneweb-cli.py gwdiff db1.pkl db2.pkl
```

Export to JSON:
```bash
python geneweb-cli.py gwdiff db1.pkl db2.pkl -o diff.json
```

Shows:
- Persons added/removed/modified
- Families added/removed/modified
- Field-level differences

### gwexport (Multi-Format Export)

#### Export to CSV

```bash
python geneweb-cli.py gwexport csv --db-file database.pkl -o ./output
```

Creates `persons.csv` and `families.csv`

#### Export to JSON

```bash
python geneweb-cli.py gwexport json --db-file database.pkl -o database.json
```

#### Export to HTML

```bash
python geneweb-cli.py gwexport html --db-file database.pkl -o family_tree.html
```

Creates a styled, responsive HTML family tree viewer

### gwc (Interactive Console)

Start interactive REPL:

```bash
python geneweb-cli.py gwc --db-file database.pkl
```

Commands:
- `find <name>` - Find person by name
- `show person <id>` - Show person details
- `show family <id>` - Show family details
- `list persons [limit]` - List persons
- `list families [limit]` - List families
- `search <query>` - Full-text search
- `stats` - Database statistics
- `help` - Show help
- `exit` - Exit console

Features:
- Command history (readline)
- Tab completion
- Multi-field search

## 🏗️ Architecture

```
geneweb-python/
├── README.md                    # This file
├── PORTING_STATUS.md            # Progress tracking
├── QUICKSTART.md                # Tutorial
├── pyproject.toml               # Package config
├── bin/                         # Entry point scripts
│   ├── gwd.py
│   ├── gwu.py
│   ├── gwb2ged.py
│   └── gwc.py
├── geneweb_python/
│   ├── __init__.py
│   └── app/
│       ├── cli.py               # Main CLI router
│       ├── gwb2ged.py           # GEDCOM exporter
│       ├── ged2gwb.py           # GEDCOM importer
│       ├── gwd.py               # HTTP daemon
│       ├── check.py             # Data validation
│       ├── gwu.py               # Utilities
│       ├── gwdiff.py            # Database diff
│       ├── gwexport.py          # Multi-format export
│       └── gwc.py               # Interactive console
└── tests/
    ├── test_gwb2ged.py          # 2 tests
    ├── test_ged2gwb.py          # 2 tests
    ├── test_gwd.py              # 1 test
    ├── test_check.py            # 3 tests
    ├── test_gwu.py              # 4 tests
    ├── test_gwdiff.py           # 7 tests
    └── test_gwexport.py         # 4 tests
```

## 🧪 Testing

Run all tests:

```bash
cd /path/to/repo/root
python -m unittest discover -s geneweb-python/tests -p "test_*.py" -v
```

Run specific test module:

```bash
python -m unittest geneweb-python.tests.test_gwb2ged -v
```

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Step-by-step tutorial
- **[PORTING_STATUS.md](PORTING_STATUS.md)** - Feature checklist
- **Inline docs** - Every module has comprehensive docstrings

## 🔧 Development

- Python version: **3.11+**
- Database: Pickle-based storage via `core.database.Database`
- Models: Complete genealogical domain model in `core.models`

## 🎯 Roadmap

### ✅ Completed
- [x] All 8 core commands
- [x] GEDCOM import/export
- [x] HTTP REST API
- [x] Data validation
- [x] Database utilities
- [x] Multi-format export
- [x] Interactive console
- [x] 23 passing tests

### 🔄 In Progress
- [ ] Extended GEDCOM tags (BAPM, BURI, OCCU, NOTE, SOUR)
- [ ] HTTP mutations (POST/PUT/DELETE)

### 📅 Planned
- [ ] Authentication & authorization
- [ ] Config file parsing
- [ ] History & merges
- [ ] DAG visualization
- [ ] Image/media management

## 📄 License

This Python reimplementation respects the original GeneWeb project's license. It reproduces behavior without copying source code.

## 🙏 Acknowledgments

Based on the OCaml GeneWeb project located in `geneweb/`. This Python version aims for behavior parity while being a complete reimplementation.