"""Application logging configuration utilities."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def _ensure_log_dir() -> Path:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    return _LOG_DIR


def setup_logging() -> Path:
    """Configure application-wide logging.

    Creates a logs directory if it does not exist and configures the root logger
    with handlers that write both to stdout and to a timestamped log file.
    """

    if getattr(setup_logging, "_configured", False):
        return getattr(setup_logging, "_log_file")

    log_dir = _ensure_log_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{timestamp}.log"

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    setup_logging._configured = True
    setup_logging._log_file = log_file
    root_logger.info("Logging initialized. Writing to %s", log_file)
    return log_file


__all__ = ["setup_logging"]

