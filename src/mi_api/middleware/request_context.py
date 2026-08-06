"""Request correlation and structured access logging middleware."""

import time
from uuid import uuid4

import structlog
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from mi_api.observability import get_logger

REQUEST_ID_HEADER = "X-Request-ID"


def _valid_request_id(value: str | None) -> str:
    if value and len(value) <= 128 and value.isascii() and value.isprintable():
        return value
    return str(uuid4())


class RequestContextMiddleware:
    """Attach a request ID and emit one access event per HTTP request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.logger = get_logger(__name__)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        supplied_request_id = headers.get(REQUEST_ID_HEADER.lower().encode("ascii"))
        request_id = _valid_request_id(
            supplied_request_id.decode("ascii", errors="ignore") if supplied_request_id else None
        )
        scope.setdefault("state", {})["request_id"] = request_id
        started = time.perf_counter()
        status_code = 500
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                message.setdefault("headers", []).append(
                    (REQUEST_ID_HEADER.encode("ascii"), request_id.encode("ascii"))
                )
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            self.logger.info(
                "http_request",
                method=scope["method"],
                path=scope["path"],
                status_code=status_code,
                duration_ms=duration_ms,
            )
            structlog.contextvars.clear_contextvars()
