from pathlib import Path

from geneweb_py import storage as storage_mod


def touch(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("")


def test_storage_manager_list_and_get(tmp_path):
    # Create a base directory with a storage.db and verify listing
    base = "mybase"
    touch(tmp_path / base / "storage.db")

    sm = storage_mod.StorageManager(tmp_path)
    bases = sm.list_bases()
    assert base in bases

    s = sm.get_storage(base)
    assert s.root == (tmp_path / base)


def test_request_binding_and_isolation(tmp_path):
    sm = storage_mod.StorageManager(tmp_path)
    s1 = sm.get_storage("A")
    s2 = sm.get_storage("B")

    # Initially no current storage
    assert storage_mod.get_current_storage() is None

    # Bind s1 and check
    token1 = storage_mod.bind_current_storage(s1)
    try:
        assert storage_mod.get_current_storage() is s1
        # Bind s2 on same context (simulate nested or different request)
        token2 = storage_mod.bind_current_storage(s2)
        try:
            assert storage_mod.get_current_storage() is s2
        finally:
            storage_mod.CURRENT_STORAGE.reset(token2)
        # After resetting token2, s1 should be current again
        assert storage_mod.get_current_storage() is s1
    finally:
        storage_mod.CURRENT_STORAGE.reset(token1)

    # After resetting token1 no storage should be bound
    assert storage_mod.get_current_storage() is None
