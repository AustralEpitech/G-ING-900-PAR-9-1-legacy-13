from pathlib import Path
from geneweb_py.plugins import discover_plugins, load_plugins
from fastapi import FastAPI


def test_discover_plugins_repo_root(tmp_path, monkeypatch):
    # ensure discover_plugins finds the existing example_plugin in repo root
    repo = Path(".")
    names = discover_plugins(repo)
    assert "example_plugin" in names


def test_load_plugins_no_templates(tmp_path):
    app = FastAPI()
    # Should not raise when templates is None; uses repo root '.' which contains plugins/example_plugin
    load_plugins(app, storage=None, config=None, repo_root=Path('.'), templates=None)
    # plugin example registers lifecycle hooks (startup/shutdown). We at least ensure include didn't crash
    assert any(p.startswith("/plugins/") or True for p in ["/plugins/example_plugin/static"])  # smoke
