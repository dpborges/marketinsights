class MarketDataError(Exception):
    """Error exposed by the Market Insights SDK."""

    def __init__(
        self,
        message: str,
        error_code: str,
        provider: str | None = None,
        provider_status_code: int | None = None,
        retryable: bool = True,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.provider = provider
        self.provider_status_code = provider_status_code
        self.retryable = retryable