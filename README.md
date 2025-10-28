# geneweb-py

This repository is a porting of the GeneWeb project from OCaml to Python.

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

The app creates minimal sample data on first startup (two persons and a family) — this is done by the
startup handler `ensure_sample_data()` in `geneweb_py/web/app.py`.

## Project layout (important files)

- `geneweb_py/` - main Python package
	- `web/app.py` - FastAPI app & routes
	- `storage.py` - simple JSON/file-backed storage implementation
	- `fs.py` - filesystem helpers (atomic writes, json load/save)
	- `config.py` - small config loader (defaults + JSON file + env vars)
	- `plugins.py` - plugin discovery/loader
- `hd/etc/` - Jinja2 templates used by the app
- `static/` - global static assets (CSS, client JS)
- `plugins/` - local plugin packages (example_plugin included)
- `data/` - runtime data: `persons.json`, `families.json`, `notes.json`, and `notes_d/`
- `requirements.txt` - Python dependencies

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

Plugins live under the `plugins/` directory (or — in a future step — will be discoverable via entry-points).
Each plugin is a normal Python package (folder with an `__init__.py`) and may implement these symbols:

- `register(app, storage, config, templates=None)` — called at import time to register routes, template helpers, etc.
- `on_startup(app)` — optional startup hook (registered with FastAPI startup event)
- `on_shutdown(app)` — optional shutdown hook

The loader also mounts any `static/` folder in a plugin under `/plugins/<name>/static` and adds plugin `templates/`
folders to the Jinja2 loader search path.

Example plugin is in `plugins/example_plugin/` — visit `/hello-plugin` when the server is running.

## Data persistence

Data is stored on disk in the `data/` directory by default:

- `persons.json` — persons metadata
- `families.json` — families metadata
- `notes.json` — notes metadata (note bodies may be stored in `data/notes_d/*.txt`)

You can safely stop the dev server; changes are written to disk via atomic writes.

## Development tips

- To reload templates quickly, the uvicorn `--reload` option picks up file changes in development.
- If you want to seed custom data for tests, you can either:
	- call `ensure_sample_data()` manually from a REPL, or
	- write small Python scripts that use `geneweb_py.storage.Storage` to create objects in `data/`.
- If FastAPI raises import/startup errors, check the terminal output — most issues are missing dependencies or path problems.

## Troubleshooting

- Port already in use: either stop the other process or run uvicorn on a different port via `--port 8001`.
- Static files 404: verify `static/` exists and that the app was started from the repository root (the server mounts `static/`).
- Permissions errors when writing `data/`: ensure the running user has write permissions in the project folder.
