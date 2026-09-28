"""Company response contracts preserving all SDK profile fields."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

Count = Annotated[int, Field(ge=0, strict=True)]


class CompanyItemError(BaseModel):
    symbol: str
    code: str
    message: str
    retryable: bool


class BatchSummary(BaseModel):
    requested: Count
    successful: Count
    failed: Count


class CompanyProfile(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    symbol: str


class CompanySummary(BaseModel):
    model_config = ConfigDict(strict=True)
    symbol: str
    name: str | None
    price: int | float | None
    sector: str | None
    industry: str | None


class CompanyProfileResponse(BaseModel):
    companies: list[CompanyProfile]
    errors: list[CompanyItemError]
    summary: BatchSummary


class CompanySummaryResponse(BaseModel):
    companies: list[CompanySummary]
    errors: list[CompanyItemError]
    summary: BatchSummary


class CompanyOperationError(BaseModel):
    code: str
    message: str
    retryable: bool


class CompanyOperationErrorResponse(BaseModel):
    error: CompanyOperationError
