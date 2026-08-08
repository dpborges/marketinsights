"""Consistent public error-response schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    """A safe, field-level error detail."""

    location: list[str | int] = Field(alias="loc")
    message: str
    error_type: str = Field(alias="type")

    model_config = ConfigDict(populate_by_name=True)


class ErrorBody(BaseModel):
    """Standard error body."""

    code: str
    message: str
    request_id: str = Field(alias="requestId")
    parameter: str | None = None
    allowed_values: list[str] | None = Field(default=None, alias="allowedValues")
    details: list[ErrorDetail | dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class ErrorEnvelope(BaseModel):
    """Top-level error response."""

    error: ErrorBody
