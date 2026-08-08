"""Application exceptions and centralized HTTP exception handlers."""

from collections.abc import Sequence
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from mi_api.observability import get_logger
from mi_api.schemas.errors import ErrorBody, ErrorDetail, ErrorEnvelope
from mi_sdk.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DataValidationError,
    SdkError,
    SymbolNotFoundError,
)

logger = get_logger(__name__)


class APIError(Exception):
    """A known error safe to translate into a public response."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        *,
        parameter: str | None = None,
        allowed_values: Sequence[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.parameter = parameter
        self.allowed_values = list(allowed_values) if allowed_values is not None else None


class InvalidQueryParameterError(APIError):
    """A query parameter contains a value outside its public contract."""

    def __init__(self, message: str, parameter: str, allowed_values: Sequence[str]) -> None:
        super().__init__(
            "INVALID_QUERY_PARAMETER",
            message,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            parameter=parameter,
            allowed_values=allowed_values,
        )


class ResourceNotFoundError(APIError):
    """A requested API resource does not exist."""

    def __init__(self, message: str = "The requested resource was not found.") -> None:
        super().__init__("RESOURCE_NOT_FOUND", message, status.HTTP_404_NOT_FOUND)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    parameter: str | None = None,
    allowed_values: Sequence[str] | None = None,
    details: Sequence[ErrorDetail | dict[str, Any]] | None = None,
) -> JSONResponse:
    envelope = ErrorEnvelope(
        error=ErrorBody(
            code=code,
            message=message,
            requestId=_request_id(request),
            parameter=parameter,
            allowedValues=list(allowed_values) if allowed_values is not None else None,
            details=list(details or []),
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=envelope.model_dump(by_alias=True, exclude_none=True),
    )


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise TypeError("Expected RequestValidationError")
    details = [
        ErrorDetail(
            loc=list(error["loc"]),
            message=error["msg"],
            type=error["type"],
        )
        for error in exc.errors()
    ]
    return _error_response(
        request,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="VALIDATION_ERROR",
        message="The request could not be validated.",
        details=details,
    )


async def api_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, APIError):
        raise TypeError("Expected APIError")
    return _error_response(
        request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        parameter=exc.parameter,
        allowed_values=exc.allowed_values,
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        raise TypeError("Expected HTTPException")
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        return _error_response(
            request,
            status_code=exc.status_code,
            code="RESOURCE_NOT_FOUND",
            message="The requested resource was not found.",
        )
    return _error_response(
        request,
        status_code=exc.status_code,
        code="HTTP_ERROR",
        message="The request could not be completed.",
    )


async def sdk_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, SdkError):
        raise TypeError("Expected SdkError")
    mappings: list[tuple[type[SdkError], int, str, str]] = [
        (
            AuthenticationError,
            status.HTTP_401_UNAUTHORIZED,
            "AUTHENTICATION_ERROR",
            "Authentication failed.",
        ),
        (
            AuthorizationError,
            status.HTTP_403_FORBIDDEN,
            "AUTHORIZATION_ERROR",
            "Access is forbidden.",
        ),
        (
            SymbolNotFoundError,
            status.HTTP_404_NOT_FOUND,
            "RESOURCE_NOT_FOUND",
            "The requested resource was not found.",
        ),
        (
            DataValidationError,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "DOMAIN_VALIDATION_ERROR",
            "The request is not valid.",
        ),
    ]
    for exception_type, status_code, code, message in mappings:
        if isinstance(exc, exception_type):
            return _error_response(
                request,
                status_code=status_code,
                code=code,
                message=message,
            )
    return _error_response(
        request,
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        code="SERVICE_UNAVAILABLE",
        message="A required service is unavailable.",
    )


async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unexpected_request_error",
        request_id=_request_id(request),
        path=request.url.path,
        exc_info=exc,
    )
    return _error_response(
        request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred.",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all application exception mappings."""

    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(APIError, api_exception_handler)
    app.add_exception_handler(SdkError, sdk_exception_handler)
    app.add_exception_handler(Exception, unexpected_exception_handler)
