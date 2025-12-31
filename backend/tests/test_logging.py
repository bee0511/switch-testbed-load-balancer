import logging
from datetime import datetime
from pathlib import Path

import pytest

from app.core import logging as app_logging


@pytest.fixture
def reset_logging_state():
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    original_level = root.level

    for attr in ("_configured", "_log_file"):
        if hasattr(app_logging.setup_logging, attr):
            delattr(app_logging.setup_logging, attr)

    yield app_logging

    for handler in list(root.handlers):
        root.removeHandler(handler)
    for handler in original_handlers:
        root.addHandler(handler)
    root.setLevel(original_level)

    for attr in ("_configured", "_log_file"):
        if hasattr(app_logging.setup_logging, attr):
            delattr(app_logging.setup_logging, attr)


def test_setup_logging_returns_cached(reset_logging_state):
    cached_path = Path("cached.log")
    reset_logging_state.setup_logging._configured = True
    reset_logging_state.setup_logging._log_file = cached_path

    assert reset_logging_state.setup_logging() == cached_path


def test_setup_logging_warns_when_log_dir_fails(reset_logging_state, monkeypatch):
    def raise_error():
        raise OSError("no permission")

    monkeypatch.setattr(reset_logging_state, "_ensure_log_dir", raise_error)

    log_file = reset_logging_state.setup_logging()
    assert log_file is None


def test_setup_logging_warns_when_file_handler_fails(
    reset_logging_state, monkeypatch, tmp_path
):
    monkeypatch.setattr(reset_logging_state, "_ensure_log_dir", lambda: tmp_path)

    def raise_file_handler(*args, **kwargs):
        raise OSError("cannot create")

    monkeypatch.setattr(reset_logging_state.logging, "FileHandler", raise_file_handler)

    log_file = reset_logging_state.setup_logging()
    assert log_file is None


def test_setup_logging_creates_log_file(reset_logging_state, monkeypatch, tmp_path):
    class FixedDatetime:
        @classmethod
        def now(cls):
            return datetime(2024, 1, 1, 0, 0, 0)

    monkeypatch.setattr(reset_logging_state, "_ensure_log_dir", lambda: tmp_path)
    monkeypatch.setattr(reset_logging_state, "datetime", FixedDatetime)

    log_file = reset_logging_state.setup_logging()

    assert log_file is not None
    assert log_file.name == "20240101_000000.log"
    assert log_file.parent == tmp_path
    assert log_file.exists()


def test_setup_logging_logs_info_when_no_reason(reset_logging_state, monkeypatch):
    monkeypatch.setattr(reset_logging_state, "_ensure_log_dir", lambda: None)

    log_file = reset_logging_state.setup_logging()

    assert log_file is None
