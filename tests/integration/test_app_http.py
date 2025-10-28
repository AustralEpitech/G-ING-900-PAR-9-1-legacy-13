import os
import sys
import shutil
import socket
import time
import subprocess
from pathlib import Path
import urllib.request

import requests
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
    # run without reload to avoid extra processes
    proc = subprocess.Popen(cmd, cwd=str(tmp), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    base = f"http://127.0.0.1:{port}"
    # wait for openapi ready
    deadline = time.time() + 15
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


def test_openapi_and_docs_http(live_server):
    base = live_server
    r = requests.get(base + "/openapi.json", timeout=5)
    assert r.status_code == 200
    j = r.json()
    assert "openapi" in j and "paths" in j

    r2 = requests.get(base + "/docs", timeout=5)
    assert r2.status_code == 200
    assert "text/html" in r2.headers.get("content-type", "")

    r3 = requests.get(base + "/", timeout=5)
    assert r3.status_code == 200

    # plugin static and plugin route
    r4 = requests.get(base + "/plugins/example_plugin/static/style.css", timeout=5)
    assert r4.status_code == 200
    r5 = requests.get(base + "/hello-plugin", timeout=5)
    assert r5.status_code == 200


def test_create_person_form_flow(live_server):
    base = live_server
    # fetch create form to get cookie/session if any
    s = requests.Session()
    r = s.get(base + "/person/create", timeout=5)
    assert r.status_code == 200
    # post form
    data = {"first_name": "IntTest", "surname": "User", "sex": "M"}
    r2 = s.post(base + "/person/create", data=data, allow_redirects=True, timeout=5)
    assert r2.status_code == 200
    # After redirect we expect to land on person page which contains the name
    assert "IntTest" in r2.text or "User" in r2.text
