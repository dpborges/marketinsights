"""System metadata schemas."""

from pydantic import BaseModel

from mi_api.config import Environment


class SystemInfoResponse(BaseModel):
    """Non-sensitive service information."""

    name: str
    version: str
    environment: Environment
