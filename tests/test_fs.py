from pathlib import Path
import os
import json
import tempfile
from geneweb_py import fs


def test_ensure_dir_and_atomic_write_and_read(tmp_path):
    d = tmp_path / "sub"
    p = d / "file.txt"
    fs.ensure_dir(d)
    assert d.exists()
    fs.atomic_write_text(p, "hello")
    assert p.read_text() == "hello"


def test_read_text_default(tmp_path):
    p = tmp_path / "nofile.txt"
    assert fs.read_text(p, default="x") == "x"


def test_json_save_and_load(tmp_path):
    p = tmp_path / "data.json"
    obj = {"a": 1, "b": "x"}
    fs.json_save(p, obj)
    loaded = fs.json_load(p, default=None)
    assert loaded == obj


def test_normalize_note_id():
    assert fs.normalize_note_id("../etc/pass") == "etc/pass"
    assert fs.normalize_note_id("/a/b/c") == "a/b/c"
    assert fs.normalize_note_id("..\\evil") == "evil"
