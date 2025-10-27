# GeneWeb Python - Quick Start Guide

This guide walks you through using the Python port of GeneWeb from scratch.

## Prerequisites

- Python 3.11+
- The existing `core/` module (database and models)

## Installation

No installation needed—run directly from the repo root.

**Important:** All commands must be run from the repository root directory using the wrapper script:

```bash
cd /path/to/G-ING-900-PAR-9-1-legacy-13

# Show all commands
python geneweb-cli.py --help
```

## Workflow Example

### 1. Create a database with the existing CLI

```bash
# Add some persons
python -m cli.main add_person --first_name Alice --surname Smith --sex F --birth 1990-01-01
python -m cli.main add_person --first_name Bob --surname Jones --sex M --birth 1985-05-15

# Add a family
python -m cli.main add_family --marriage 2010-06-20 --marriage_place Paris

# This creates database.pkl
```

### 2. Export to GEDCOM

```bash
python geneweb-cli.py gwb2ged --db-file database.pkl -o output.ged
```

Check the GEDCOM file:
```bash
cat output.ged
# You should see HEAD, INDI records, FAM records, and TRLR
```

### 3. Import a GEDCOM

```bash
# Import into a new database
python geneweb-cli.py ged2gwb output.ged --db-file imported.pkl --verbose
```

### 4. Run data checks

```bash
python geneweb-cli.py check --db-file database.pkl
```

Expected output:
```
✓ No issues found. Database looks good!
# Or a list of warnings/errors if data has inconsistencies
```

### 5. Start the HTTP daemon

```bash
python geneweb-cli.py gwd --db-file database.pkl --port 2317
```

Open another terminal and query the API:

```bash
# List all persons
curl http://127.0.0.1:2317/persons

# Get person by ID
curl http://127.0.0.1:2317/persons/1

# Search by name
curl http://127.0.0.1:2317/search?q=Smith

# Filter by surname
curl http://127.0.0.1:2317/persons?surname=Jones
```

Press Ctrl+C to stop the daemon.

## Running Tests

```bash
python -m unittest discover -s geneweb-python/tests -v
```

Expected: 8 tests passing

## What's Implemented

| Feature | Status |
|---------|--------|
| GEDCOM Export (gwb2ged) | ✅ Full family linkage |
| GEDCOM Import (ged2gwb) | ✅ Bidirectional conversion |
| HTTP REST API (gwd) | ✅ Search + filtering |
| Data Validation (check) | ✅ Consistency checks |
| Tests | ✅ 8 passing |

## Next Steps

See `PORTING_STATUS.md` for the roadmap of features to be ported from the OCaml GeneWeb.

Suggestions for contributions:
- Add more OCaml lib modules (merges, history, DAG views)
- Implement gwu utilities
- Add more GEDCOM tags (events, notes, sources)
- Enhance the HTTP API with mutations (POST/PUT/DELETE)
