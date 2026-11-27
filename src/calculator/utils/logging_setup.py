"""Logging configuration."""

import json
import logging

class JsonFormatter(logging.Formatter):
    """Formats log records as JSON strings for the file."""
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({
            "timestamp": self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        })


def configure_app_logger(name: str, log_file, *, instance, level=logging.INFO, encoding="utf-8") -> logging.Logger:
    logger = logging.getLogger(f"{name}.{id(instance)}")
    logger.setLevel(level)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    try:
        file_handler = logging.FileHandler(log_file, mode="a", encoding=encoding)
    except FileNotFoundError:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode="a", encoding=encoding)
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


def configure_worker_logger(logger: logging.Logger, *, child="worker", level=logging.DEBUG) -> logging.Logger:
    worker_logger = logger.getChild(child)
    worker_logger.setLevel(level)
    worker_logger.propagate = False
    worker_logger.handlers.clear()
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            worker_logger.addHandler(handler)
    return worker_logger
