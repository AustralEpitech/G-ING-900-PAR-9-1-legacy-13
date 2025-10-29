import time
import requests


def test_per_client_base_selection_and_isolation(live_server):
    base = live_server

    # Client A selects base 'A' via query param, server should set gw_base cookie
    s1 = requests.Session()
    r = s1.get(base + '/?b=A', timeout=5)
    assert r.status_code in (200, 302)
    # Cookie should be set by middleware
    assert s1.cookies.get('gw_base') == 'A'

    # Client B selects base 'B'
    s2 = requests.Session()
    r2 = s2.get(base + '/?b=B', timeout=5)
    assert r2.status_code in (200, 302)
    assert s2.cookies.get('gw_base') == 'B'

    # Create a person in A
    data_a = {'first_name': 'Alice', 'surname': 'A', 'sex': 'F'}
    pa = s1.post(base + '/person/create', data=data_a, allow_redirects=True, timeout=5)
    assert pa.status_code == 200

    # Create a person in B
    data_b = {'first_name': 'Bob', 'surname': 'B', 'sex': 'M'}
    pb = s2.post(base + '/person/create', data=data_b, allow_redirects=True, timeout=5)
    assert pb.status_code == 200

    # Give server a short moment to persist
    time.sleep(0.1)

    # s1 should see Alice but not Bob
    r1 = s1.get(base + '/people', timeout=5)
    assert r1.status_code == 200
    assert 'Alice' in r1.text
    assert 'Bob' not in r1.text

    # s2 should see Bob but not Alice
    r2 = s2.get(base + '/people', timeout=5)
    assert r2.status_code == 200
    assert 'Bob' in r2.text
    assert 'Alice' not in r2.text
