"""Basic smoke tests: the module imports cleanly and tools are registered.

These don't hit the real iAqualink API — no credentials required.
"""

from iaqualink_mcp import server


def test_module_imports():
    assert server.mcp is not None


def test_read_only_defaults_false(monkeypatch):
    monkeypatch.delenv("IAQUALINK_READ_ONLY", raising=False)
    assert server._read_only() is False


def test_read_only_true(monkeypatch):
    monkeypatch.setenv("IAQUALINK_READ_ONLY", "true")
    assert server._read_only() is True


def test_creds_missing_raises(monkeypatch):
    monkeypatch.delenv("IAQUALINK_USERNAME", raising=False)
    monkeypatch.delenv("IAQUALINK_PASSWORD", raising=False)
    try:
        server._creds()
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass


def test_creds_present(monkeypatch):
    monkeypatch.setenv("IAQUALINK_USERNAME", "user@example.com")
    monkeypatch.setenv("IAQUALINK_PASSWORD", "secret")
    assert server._creds() == ("user@example.com", "secret")
