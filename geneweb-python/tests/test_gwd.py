import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
import json
from http.client import HTTPConnection

# Ensure the geneweb-python package can be imported when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from core.database import Database
    from core.models import CDate
except Exception as exc:  # pragma: no cover
    raise RuntimeError("Tests must run from repo root where core.database is importable") from exc


class TestGWD(unittest.TestCase):
    """Test the HTTP daemon in a subprocess-like manner (manual start/stop)."""

    def test_daemon_serves_persons_endpoint(self):
        """Start daemon in a thread, query /persons, verify response."""
        import threading
        from geneweb_python.app.gwd import serve

        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "db.pkl")
            db = Database(storage_file=db_path)
            pid = db.add_person(first_name="Alice", surname="Test", sex="F", birth=CDate(year=1990))

            # Start daemon in a background thread
            host, port = "127.0.0.1", 9999
            server_thread = threading.Thread(target=serve, args=(db, host, port), daemon=True)
            server_thread.start()

            # Give server time to start
            import time
            time.sleep(0.5)

            # Query the API
            conn = HTTPConnection(host, port, timeout=2)
            conn.request("GET", "/persons")
            resp = conn.getresponse()
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["first_name"], "Alice")
            self.assertEqual(data[0]["surname"], "Test")
            conn.close()


if __name__ == "__main__":
    unittest.main()
