"""Stderr logging with per–tool-call request correlation."""

from __future__ import annotations

import contextvars
import logging
import uuid
from contextlib import contextmanager
from typing import Iterator

_request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)


class RequestIdFilter(logging.Filter):
    """Inject request_id into every log record for [req_id=…] formatting."""

    def filter(self, record: logging.LogRecord) -> bool:
        rid = _request_id_var.get()
        record.request_id = rid if rid else "-"
        return True


@contextmanager
def request_scope() -> Iterator[None]:
    """Bind a fresh UUID4 for the duration of one tool invocation."""
    token = _request_id_var.set(str(uuid.uuid4()))
    try:
        yield
    finally:
        _request_id_var.reset(token)


def configure_logging() -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s [%(levelname)s] [req_id=%(request_id)s] "
            "%(name)s: %(message)s"
        ),
        handlers=[logging.StreamHandler()],
    )
    for handler in logging.root.handlers:
        handler.addFilter(RequestIdFilter())
    return logging.getLogger("spira-mcp")


log = configure_logging()
