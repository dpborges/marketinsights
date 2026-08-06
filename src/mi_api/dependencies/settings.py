"""Settings dependency."""

from typing import cast

from fastapi import Request

from mi_api.config import APISettings


def get_settings(request: Request) -> APISettings:
    """Return settings attached during application construction."""

    return cast(APISettings, request.app.state.settings)
