"""Health endpoint schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Liveness response."""

    status: Literal["ok"] = "ok"
    service: str
    version: str


class ReadinessResponse(BaseModel):
    """Readiness response without infrastructure details."""

    status: Literal["ok", "unavailable"]
    service: str
    version: str
    checks: dict[str, Literal["ok", "unavailable", "not_configured"]] = Field(default_factory=dict)
