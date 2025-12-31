import logging

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api import deps


@pytest.mark.asyncio
async def test_get_machine_manager_caches_instance(monkeypatch):
    class DummyManager:
        pass

    deps._manager_instance = None
    monkeypatch.setattr(deps, "MachineManager", DummyManager)

    first = await deps.get_machine_manager()
    second = await deps.get_machine_manager()

    assert isinstance(first, DummyManager)
    assert first is second


@pytest.mark.asyncio
async def test_verify_bearer_token_missing_env_logs_error(monkeypatch, caplog):
    monkeypatch.delenv("API_BEARER_TOKEN", raising=False)
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="token-value"
    )

    with caplog.at_level(logging.ERROR):
        with pytest.raises(HTTPException) as exc:
            await deps.verify_bearer_token(credentials)

    assert exc.value.status_code == 401
    assert "API_BEARER_TOKEN is not set" in caplog.text


@pytest.mark.asyncio
async def test_verify_bearer_token_accepts_valid_token(monkeypatch):
    monkeypatch.setenv("API_BEARER_TOKEN", "token-value")
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="token-value"
    )

    result = await deps.verify_bearer_token(credentials)

    assert result == "token-value"
