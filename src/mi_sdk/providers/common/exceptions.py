class ProviderError(Exception):
    """Base exception for external market-data providers."""

    def __init__(
        self,
        message: str,
        provider: str,
        error_code: str,
        status_code: int | None = None,
        retryable: bool = False,
    ):
        super().__init__(message)

        self.message = message
        self.provider = provider
        self.error_code = error_code
        self.status_code = status_code
        self.retryable = retryable

"""Below is example of extending the class hierarchy for 
provider-specific errors. You can create subclasses for each provider 
to handle their specific error codes and messages. For example:"""

class ProviderRateLimitError(ProviderError):

    def __init__(
        self, 
        message: str,
        provider: str,
        status_code: int | None = None,
    ):
        super().__init__(
            message=message,
            provider=provider,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=status_code,
            retryable=True,
        )


