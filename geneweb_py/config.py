"""Simple configuration loader for geneweb_py.

Behavior:
- Load defaults.
- If environment variable `GENEWEB_CONFIG` is set, load that JSON file and merge.
- Environment variables override file values (variables: GENEWEB_DATA_DIR, GENEWEB_TEMPLATES_DIR, GENEWEB_STATIC_DIR).

This is intentionally small and dependency-free (JSON config). If you prefer
YAML support we can add PyYAML as an optional dependency.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
import json
from typing import Optional


@dataclass
class Config:
    data_dir: Path = Path("data")
    templates_dir: Path = Path("hd") / "etc"
    static_dir: Path = Path("static")


def _load_json_file(path: Path) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from (1) defaults, (2) JSON file, (3) env vars.

    :param config_path: optional path to a JSON config file. If not provided
                        will use environment variable `GENEWEB_CONFIG` if set.
    """
    cfg = Config()

    # 1) config file
    cp = config_path or os.environ.get("GENEWEB_CONFIG")
    if cp:
        p = Path(cp)
        data = _load_json_file(p)
        if isinstance(data, dict):
            if "data_dir" in data:
                cfg.data_dir = Path(data["data_dir"]) if data["data_dir"] else cfg.data_dir
            if "templates_dir" in data:
                cfg.templates_dir = Path(data["templates_dir"]) if data["templates_dir"] else cfg.templates_dir
            if "static_dir" in data:
                cfg.static_dir = Path(data["static_dir"]) if data["static_dir"] else cfg.static_dir

    # 2) environment variables override only if no explicit config_path was
    # provided to the function. When a config_path is passed we consider the
    # file authoritative for the test/explicit case and do not let global env
    # variables silently override those values (tests rely on this).
    if config_path is None:
        if os.environ.get("GENEWEB_DATA_DIR"):
            cfg.data_dir = Path(os.environ.get("GENEWEB_DATA_DIR"))
        if os.environ.get("GENEWEB_TEMPLATES_DIR"):
            cfg.templates_dir = Path(os.environ.get("GENEWEB_TEMPLATES_DIR"))
        if os.environ.get("GENEWEB_STATIC_DIR"):
            cfg.static_dir = Path(os.environ.get("GENEWEB_STATIC_DIR"))

    return cfg
