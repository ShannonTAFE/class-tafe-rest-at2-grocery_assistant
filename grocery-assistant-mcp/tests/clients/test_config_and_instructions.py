from clients.shared.config import env_bool
from clients.shared.instructions import grocery_agent_instructions


def test_env_bool(monkeypatch):
    monkeypatch.delenv("EXAMPLE_BOOL", raising=False)
    assert env_bool("EXAMPLE_BOOL", default=True) is True

    monkeypatch.setenv("EXAMPLE_BOOL", "true")
    assert env_bool("EXAMPLE_BOOL") is True

    monkeypatch.setenv("EXAMPLE_BOOL", "0")
    assert env_bool("EXAMPLE_BOOL") is False


def test_instructions_reflect_write_mode():
    read_only = grocery_agent_instructions(provider_name="Test", allow_writes=False)
    write_enabled = grocery_agent_instructions(provider_name="Test", allow_writes=True)

    assert "Write mode for this run: disabled" in read_only
    assert "Write tools are not exposed" in read_only
    assert "Write mode for this run: enabled" in write_enabled
    assert "clearly asks to add" in write_enabled
