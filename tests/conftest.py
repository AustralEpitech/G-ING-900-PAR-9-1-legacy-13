import os
import tempfile
import shutil
import atexit

_gw_test_data_dir = None


def pytest_configure(config):
    """Create a session-scoped temporary data directory for tests and
    set the GENEWEB_DATA_DIR environment variable so the app and any
    subprocesses will write into an isolated location.

    This avoids tests mutating the repository-local `data/` folder.
    """
    global _gw_test_data_dir
    # create a temp dir once for the test session
    td = tempfile.mkdtemp(prefix="gw_test_data_")
    _gw_test_data_dir = td
    os.environ.setdefault("GENEWEB_DATA_DIR", td)


def pytest_unconfigure(config):
    """Remove the temporary data directory created for the test session.

    We attempt a best-effort cleanup; if removal fails we leave the
    directory for manual inspection.
    """
    global _gw_test_data_dir
    td = _gw_test_data_dir
    _gw_test_data_dir = None
    if td and os.path.exists(td):
        try:
            shutil.rmtree(td)
        except Exception:
            # don't raise during pytest shutdown
            pass


# also register an atexit fallback in case pytest_unconfigure isn't called
def _atexit_cleanup():
    global _gw_test_data_dir
    td = _gw_test_data_dir
    if td and os.path.exists(td):
        try:
            shutil.rmtree(td)
        except Exception:
            pass


atexit.register(_atexit_cleanup)
import sys
from pathlib import Path

# Ensure repo root is on sys.path so tests can import the package directly
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))
