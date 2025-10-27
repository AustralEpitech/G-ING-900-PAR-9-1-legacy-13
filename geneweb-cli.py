#!/usr/bin/env python
"""Wrapper script to run geneweb-python CLI from repo root."""
import sys
from pathlib import Path

# Add paths to import core and geneweb_python
repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "geneweb-python"))

from geneweb_python.app.cli import main

if __name__ == "__main__":
    sys.exit(main())
