import os
import sys
import shutil
import socket
import time
import subprocess
from pathlib import Path
import urllib.request

import pytest


def _find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    addr, port = s.getsockname()
    s.close()
    return port


@pytest.fixture(scope="module")
def live_server(tmp_path_factory):
    """Start a uvicorn server from a temporary copy of the repo and yield base url.

    The fixture copies minimal runtime files into a temp dir, starts uvicorn as a subprocess
    in that directory, waits for readiness by polling /openapi.json, and then yields the
    base URL (http://127.0.0.1:PORT). After tests complete the server is terminated.
    """
    # build temp workspace
    tmp = tmp_path_factory.mktemp("gw_live")
    # repo root is two levels up from tests/integration/conftest.py
    repo_root = Path(__file__).resolve().parents[2]

    # Copy only the runtime pieces needed: geneweb_py package, plugins, hd, static
    for name in ("geneweb_py", "plugins", "hd", "static"):
        src = repo_root / name
        if src.exists():
            dst = tmp / name
            shutil.copytree(src, dst)

    port = _find_free_port()
    cmd = [sys.executable, "-m", "uvicorn", "geneweb_py.web.app:app", "--host", "127.0.0.1", "--port", str(port)]
    env = os.environ.copy()
    # Ensure the temporary repo root is on PYTHONPATH so the copied package is importable
    env_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(tmp) + (os.pathsep + env_pythonpath if env_pythonpath else "")
    # run without reload to avoid extra processes
    # Do not capture stdout/stderr so server startup errors are visible in test output
    proc = subprocess.Popen(cmd, cwd=str(tmp), env=env, stdout=None, stderr=None)

    base = f"http://127.0.0.1:{port}"
    # wait for openapi ready
    # allow a bit more time on slower CI/windows hosts
    deadline = time.time() + 30
    last_exc = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(base + "/openapi.json", timeout=1) as r:
                if r.status == 200:
                    break
        except Exception as e:
            last_exc = e
            time.sleep(0.2)
            continue
    else:
        # timed out
        proc.kill()
        out, err = proc.communicate(timeout=1)
        pytest.fail(f"Server did not become ready in time; last error: {last_exc}\nstdout:\n{out}\nstderr:\n{err}")

    try:
        yield base
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
