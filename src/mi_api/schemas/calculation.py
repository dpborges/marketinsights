"""Stop-loss response contract using the SDK's domain models."""

from pydantic import BaseModel

from mi_api.schemas.company import BatchSummary, CompanyItemError
from mi_sdk.domain.models.stop_loss import CompanyStopLoss


class StopLossResponse(BaseModel):
    companies: list[CompanyStopLoss]
    errors: list[CompanyItemError]
    summary: BatchSummary
