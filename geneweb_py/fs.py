"""Filesystem helper utilities used by storage and other modules.

Small, well-tested helpers for safe JSON read/write, atomic text writes,
and path normalization for note ids.
"""
from __future__ import annotations
from pathlib import Path
import json
import tempfile
import os
from typing import Any, Optional


def ensure_dir(path: Path) -> None:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)


def atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    """Write text to path atomically using a temp file in the same dir.

    This avoids partial writes when the process is interrupted.
    """
    path = Path(path)
    ensure_dir(path.parent)
    # Create a temp file in the same directory for atomic rename
    fd, tmp = tempfile.mkstemp(dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(text)
        os.replace(tmp, str(path))
    finally:
        # If replace failed and tmp still exists, remove it
        try:
            if Path(tmp).exists():
                Path(tmp).unlink()
        except Exception:
            pass


def read_text(path: Path, default: Optional[str] = None, encoding: str = "utf-8") -> Optional[str]:
    p = Path(path)
    if not p.exists():
        return default
    try:
        return p.read_text(encoding=encoding)
    except Exception:
        return default


def json_load(path: Path, default: Optional[Any] = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def json_save(path: Path, obj: Any) -> None:
    p = Path(path)
    ensure_dir(p.parent)
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    atomic_write_text(p, text)


def normalize_note_id(nid: str) -> str:
    """Normalize a note id to a safe filename-like string.

    This strips any leading/trailing slashes and forbids path traversal by
    removing parent directory segments. It's conservative — callers should
    validate ids further if needed.
    """
    parts = [p for p in Path(nid).parts if p not in ("..", "/", "\\")]
    return "/".join(parts).lstrip("/")
