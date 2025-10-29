import requests


def test_create_new_base_via_ui(live_server):
    base = live_server
    s = requests.Session()

    # Ensure we're on the choose-base page by clearing any existing cookie
    r = s.get(base + "/change_db", allow_redirects=True, timeout=5)
    assert r.status_code in (200, 302)

    # Create a unique base name
    name = "ci_new_base"
    r2 = s.post(base + "/create_base", data={"name": name}, allow_redirects=True, timeout=5)
    # After redirect middleware sets cookie
    assert s.cookies.get("gw_base") == name

    # Clear cookie and ensure the new base appears in the choose list
    s.get(base + "/change_db", allow_redirects=True, timeout=5)
    r3 = s.get(base + "/", timeout=5)
    assert r3.status_code == 200
    assert name in r3.text
