import asyncio

import pytest

from app import main


def test_require_env_raises_when_missing(monkeypatch):
    monkeypatch.delenv("MISSING_VAR", raising=False)
    with pytest.raises(RuntimeError):
        main._require_env("MISSING_VAR")


def test_require_env_returns_value(monkeypatch):
    monkeypatch.setenv("PRESENT_VAR", "value")
    assert main._require_env("PRESENT_VAR") == "value"


@pytest.mark.asyncio
async def test_lifespan_runs_startup_and_shutdown(monkeypatch):
    monkeypatch.setenv("API_BEARER_TOKEN", "token")

    class DummyManager:
        def __init__(self):
            self.initialize_called = False

        async def initialize_status(self):
            self.initialize_called = True

    manager = DummyManager()
    monitor_started = asyncio.Event()

    async def fake_get_manager():
        return manager

    async def fake_monitor(_manager):
        monitor_started.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(main, "get_machine_manager", fake_get_manager)
    monkeypatch.setattr(main, "monitor_machines", fake_monitor)

    async with main.lifespan(main.app):
        await asyncio.wait_for(monitor_started.wait(), timeout=1)
        assert manager.initialize_called is True
