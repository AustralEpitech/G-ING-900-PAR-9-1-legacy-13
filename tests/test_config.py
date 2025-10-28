import os
from pathlib import Path
import json
import tempfile
from geneweb_py.config import load_config, Config, _load_json_file


def test_load_config_from_file(tmp_path, monkeypatch):
    cfgfile = tmp_path / "cfg.json"
    data = {"data_dir": "mydata", "templates_dir": "mytpl", "static_dir": "mystatic"}
    cfgfile.write_text(json.dumps(data))
    cfg = load_config(str(cfgfile))
    assert cfg.data_dir == Path("mydata")
    assert cfg.templates_dir == Path("mytpl")
    assert cfg.static_dir == Path("mystatic")


def test_env_overrides(tmp_path, monkeypatch):
    monkeypatch.setenv("GENEWEB_DATA_DIR", "envdata")
    monkeypatch.setenv("GENEWEB_TEMPLATES_DIR", "envtpl")
    monkeypatch.setenv("GENEWEB_STATIC_DIR", "envstatic")
    cfg = load_config(None)
    assert cfg.data_dir == Path("envdata")
    assert cfg.templates_dir == Path("envtpl")
    assert cfg.static_dir == Path("envstatic")
