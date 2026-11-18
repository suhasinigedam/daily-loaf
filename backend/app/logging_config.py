"""JSON logs with the request ID on every line."""

import logging
import sys

from pythonjsonlogger.json import JsonFormatter

from app.api.middleware import request_id_var

_handler: logging.Handler | None = None


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def configure_logging(level: str) -> None:
    global _handler
    root = logging.getLogger()
    if _handler is None:
        _handler = logging.StreamHandler(sys.stdout)
        _handler.setFormatter(
            JsonFormatter(
                "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
                rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
            )
        )
        _handler.addFilter(RequestIdFilter())
        root.addHandler(_handler)
    root.setLevel(level)
