"""Application logging configuration utilities."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def _ensure_log_dir() -> Path:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    return _LOG_DIR


def setup_logging() -> Path | None:
    """Configure application-wide logging.

    Creates a logs directory if it does not exist and configures the root logger
    with handlers that write both to stdout and to a timestamped log file.
    If the directory or log file cannot be created, falls back to stdout-only
    logging and returns ``None``.
    """

    if getattr(setup_logging, "_configured", False):
        return getattr(setup_logging, "_log_file")

    try:
        log_dir = _ensure_log_dir()
    except OSError as exc:
        log_dir = None
        log_dir_error = exc
    else:
        log_dir_error = None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = None
    file_error: OSError | None = None

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    if log_dir is not None:
        candidate_log_file = log_dir / f"{timestamp}.log"
        try:
            file_handler = logging.FileHandler(candidate_log_file, encoding="utf-8")
        except OSError as exc:
            file_error = exc
        else:
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            log_file = candidate_log_file

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    setup_logging._configured = True
    setup_logging._log_file = log_file
    if log_file is not None:
        root_logger.info("Logging initialized. Writing to %s", log_file)
    else:
        reason = file_error or log_dir_error
        if reason is not None:
            root_logger.warning(
                "Logging initialized without file handler due to: %s", reason
            )
        else:
            root_logger.info("Logging initialized without file handler.")
    return log_file


__all__ = ["setup_logging"]

