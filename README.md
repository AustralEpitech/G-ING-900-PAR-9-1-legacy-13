# geneweb-py

This repository is a porting of the GeneWeb project from OCaml to Python. The Python
port aims to provide a compact, testable implementation with a small web UI and a
JSON/HTTP API for programmatic access.

## Prerequisites

- Python 3.10+ installed and available on your PATH (the project was developed with Python 3.11).
- Git (optional) if you cloned the repo.

## Quick start (Windows PowerShell)

1. Create and activate a venv

```powershell
python -m venv .venv
# If you get an execution policy error when activating, run (in the same PowerShell session):
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```


3. Run the development server

```powershell
python -m uvicorn geneweb_py.web.app:app --reload --port 8000
```

4. Open in your browser

- Main UI: http://127.0.0.1:8000/
- People list: http://127.0.0.1:8000/people
- Families list: http://127.0.0.1:8000/families
- Notes UI: http://127.0.0.1:8000/notes
- Example plugin: http://127.0.0.1:8000/hello-plugin (plugin template + CSS are included under `plugins/example_plugin`)

Behavior note: on first visit the root page will prompt you to choose a database (called a "base").
The selected base is stored per-client (in a cookie named `gw_base`) so different browsers/clients
can use different databases simultaneously. You can also temporarily override the base for a
single request using the `?b=<base>` query parameter. Use the "Change database" button on the
welcome page to clear the cookie and return to the base selection UI.

### API

- Programmatic JSON API endpoints are available under `/api`:
	- `GET /api/person/{pid}` — fetch a person and immediate relations
	- `GET /api/family/{fid}` — fetch a family and its members
- OpenAPI documentation (Swagger UI) is available at: http://127.0.0.1:8000/docs
- ReDoc documentation is available at: http://127.0.0.1:8000/redoc


## Configuration

The project uses `geneweb_py.config.load_config()` which supports:

- Defaults (data in `data/`, templates in `hd/etc`, static in `static/`).
- Overriding via a JSON config file referenced by the `GENEWEB_CONFIG` environment variable.
- Direct environment variable overrides:
	- `GENEWEB_DATA_DIR`
	- `GENEWEB_TEMPLATES_DIR`
	- `GENEWEB_STATIC_DIR`

Database selection behavior
- The server manages multiple named bases: each base is a subdirectory under the configured
  `data_dir` and contains its own `storage.db` SQLite file.
- On first use a base directory will be created automatically when you create content (or when
  you explicitly create a base in the UI).
- To create a base from the UI: visit the root (choose-base) page and use the "Create new base"
  form. The server will initialize the base and then redirect and set the `gw_base` cookie.

Example: run with a custom config file in PowerShell

```powershell
$env:GENEWEB_CONFIG = 'C:\path\to\myconfig.json'
python -m uvicorn geneweb_py.web.app:app --reload --port 8000
```

`myconfig.json` (example):

```json
{
	"data_dir": "data",
	"templates_dir": "hd/etc",
	"static_dir": "static"
}
```

## Plugins

Plugins live under the `plugins/` directory.
Each plugin is a normal Python package (folder with an `__init__.py`) and may implement these symbols:

- `register(app, storage, config, templates=None)` — called at import time to register routes, template helpers, etc.
- `on_startup(app)` — optional startup hook (registered with FastAPI startup event)
- `on_shutdown(app)` — optional shutdown hook

The loader also mounts any `static/` folder in a plugin under `/plugins/<name>/static` and adds plugin `templates/`
folders to the Jinja2 loader search path.

Example plugin is in `plugins/example_plugin/` — visit `/hello-plugin` when the server is running.

## Data persistence

By default the application persists data in a local SQLite database file located at `data/storage.db`.
The storage layer uses a normalized set of tables for persons, families and children. To support richer GeneWeb-like semantics the app stores structured fields (dates, places, and per-person/family events) as JSON in dedicated columns. This allows the code to round-trip structured `CDate`, `Place` and `PersEvent` objects while keeping the DB schema compact.

Changes are written to `data/storage.db` atomically and the notes files are written atomically under `data/notes_d/`.

## GEDCOM import / export

This project includes a small GEDCOM importer/exporter to help migrate genealogical
data into and out of the application. The CLI helper is `scripts/import_gedcom.py` and
uses a conservative, dependency-free parser by default.

Basic usage (PowerShell):

```powershell
# Import a GEDCOM into the app's data directory (creates/updates data/storage.db)
python .\scripts\import_gedcom.py import --file C:\path\to\file.ged --data-dir data

# Export the current DB to a GEDCOM file (parent directories are created automatically)
python .\scripts\import_gedcom.py export --out C:\path\to\out.ged --data-dir data
```

Notes:
- The importer stores GEDCOM record ids with a `gedcom:` prefix (for traceability). The importer
	is idempotent: importing a file exported by the tool will not create duplicated entries.
- File-backed notes under `data/notes_d/*.txt` continue to override DB notes as before.
- Always back up your `data/storage.db` (or legacy JSON data) before running large imports.

## Relationship algorithms

The Python port includes several relationship and kinship utilities inspired by
the GeneWeb reference implementation. These helpers are small, importable
functions you can call from scripts or a REPL.

- `geneweb_py.sosa.sosa_ancestors(storage, root_id, max_depth=...)`
	- Enumerates ancestors using Sosa (Ahnentafel) numbering. Returns a list of
		dicts with sosa numbers, levels and parent Sosa links. Useful for
		displaying ancestor tables.

- `geneweb_py.relationship.shortest_path(storage, a_id, b_id, max_depth=None)`
	- Returns a single shortest path (distance and list of person ids) between two
		persons using parent/child and spouse edges. Uses a bidirectional BFS for
		performance.

- `geneweb_py.relationship.all_shortest_paths(storage, a_id, b_id, max_paths=100)`
	- Enumerates all shortest paths (up to `max_paths`) between two persons.

- `geneweb_py.consanguinity.relationship_and_links(storage, a_id, b_id, max_anc_depth=None)`
	- Computes the coefficient of relationship (r) and returns a list of common
		ancestors with their per-path counts and individual contributions. Handles
		multiple ancestral paths (implex) and estimates ancestor inbreeding.

- `geneweb_py.cousins.cousin_label(l1, l2)`
	- Given generation distances to the MRCA (e.g. parent=1, grandparent=2),
		returns a human-friendly label (sibling, aunt/uncle, 1st cousin once removed,
		etc.) plus structured `(degree, removed)` values.

Usage examples (Python):

```python
from geneweb_py.storage import Storage
from geneweb_py.relationship import shortest_path
from geneweb_py.consanguinity import relationship_and_links
from geneweb_py.cousins import cousin_label

store = Storage('data')
dist, path = shortest_path(store, pid1, pid2)
r, common = relationship_and_links(store, pid1, pid2, max_anc_depth=8)
label, degree, removed = cousin_label(2, 3)  # e.g. 1st cousin once removed
```

Notes:
- For consanguinity and ancestor enumeration prefer limiting `max_depth` to
	6–10 generations for interactive use to avoid large combinatorics on dense
	pedigrees.
- All functions operate on the `Storage` API used by the app (see
	`geneweb_py/storage.py`) and accept person ids as strings.

## Running tests

Unit and integration tests use `pytest`. Integration tests in this repository are implemented
to run against a live test server (a small uvicorn subprocess) using a `live_server` fixture
that copies a minimal runtime layout into a temporary directory and starts the app there. That
fixture and the test suite are designed to avoid mutating your repository `data/` folder.

Important testing notes:
- The repository provides `pytest.ini` which disables the `pytest-django` plugin by default
	(some environments install that plugin and it auto-skips tests when no Django settings are
	configured). This makes `pytest` run deterministically without needing `-p no:django`.
- Tests create an isolated temporary `GENEWEB_DATA_DIR` for the whole pytest session so DB writes
	and note files are written to a temp directory and cleaned up after the run. This prevents
	tests from modifying your repository `data/` folder.
- The integration `live_server` fixture ensures subprocesses inherit the test environment
	(including `GENEWEB_DATA_DIR` and `PYTHONPATH`) so test runs are hermetic.

To run the full test suite:

Install dependencies (PowerShell):

```powershell
python -m pip install -r requirements.txt
python -m pip install pytest
```

Run all tests:

```powershell
pytest -q
```

Run only integration tests (if present):

```powershell
pytest tests/integration -q -p no:django
```

If you have any problems with tests touching your production data, ensure you're running
inside the project's virtual environment and then run pytest normally; the test suite will
use a temporary data directory automatically.

If tests fail, ensure you're running inside the project's virtual environment and that
`fastapi`, `jinja2`, and testing dependencies are installed.

