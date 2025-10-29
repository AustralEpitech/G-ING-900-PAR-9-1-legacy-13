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

## Running tests

Unit and integration tests use `pytest`. Integration tests in this repository are implemented
to run in-process (they call handlers directly or use FastAPI's TestClient) and therefore do
not require a running `uvicorn` server in most cases. To run the full test suite:

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

If your environment auto-loads pytest plugins you don't want, you can temporarily disable
plugin autoload for the command as shown above in the original README.

If tests fail, ensure you're running inside the project's virtual environment and that
`fastapi`, `jinja2`, and testing dependencies are installed.

