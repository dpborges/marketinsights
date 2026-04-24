"""SDK Exception Hierarchy"""

from typing import Any, Optional


class SdkError(Exception):
    """Base exception for all SDK errors"""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.details = details or {}


class ConfigurationError(SdkError):
    """Raised when there's a configuration issue"""
    pass


class AuthenticationError(SdkError):
    """Raised when authentication fails"""
    pass


class AuthorizationError(SdkError):
    """Raised when authorization fails"""
    pass


class RateLimitError(SdkError):
    """Raised when rate limit is exceeded"""
    pass


class ProviderUnavailableError(SdkError):
    """Raised when a provider is unavailable"""
    pass


class DataValidationError(SdkError):
    """Raised when data validation fails"""
    pass


class SymbolNotFoundError(SdkError):
    """Raised when a symbol is not found"""
    pass


class UnsupportedOperationError(SdkError):
    """Raised when an operation is not supported"""
    pass