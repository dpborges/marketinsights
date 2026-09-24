## MI Layered archicture
<pre>
Rest API Layer
    ||
    \/
MI SDK Layer
    ||
    \/
FMP Provider
    ||
    \/
FMP HTTP API
</pre>

### MI Type of Errors:  
- ProviderError 
- MarketDataError

![Type of Errors Diagram](TypesOfErrorsDiagram.png)

### Provider Exception Class
```python
class ProviderError(Exception):
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
```

This Python class defines a **custom exception** designed to handle failures when interacting with external providers (eg FMP).

Instead of raising a generic error, this custom error captures structured metadata about *what* went wrong and *where*.

The class is located in: src/mi_sdk/providers/common/exceptions.py

#### Attributes:

Attaches each value to the exception instance, allowing upstream code to inspect these details programmatically.

* `message: str` — A human-readable description of the error.
* `provider: str` — The name of the third-party service (e.g., `"openai"`, `"stripe"`).
* `error_code: str` — A specific internal error identifier from the provider (e.g., `"rate_limit_exceeded"`, `"insufficient_funds"`).
* `status_code: int | None = None` — The HTTP status code returned by the API (e.g., `404`, `500`), defaulting to `None` if not an HTTP error.
* `retryable: bool = True` — A flag indicating whether the operation can be safely retried immediately or after a delay. Default value is True.

Note that the HTTP status_code travels with the exception as diagnostic metadata, even though the SDK isn't HTTP-aware. 


### Example Usage

#### Raising the exception:

```python
raise ProviderError(
    message="API request timed out while connecting to OpenAI.",
    provider="OpenAI",
    error_code="TIMEOUT",
    status_code=504,
    retryable=True
)
```

#### Catching and using the metadata:

```python
try:
    # Code making an external API call
    call_external_service()
except ProviderError as err:
    print(f"Error from {err.provider}: {err.message}")
    
    # Conditional logic based on error attributes
    if err.retryable:
        print("Retrying request...")
    else:
        print(f"Failed permanently with code: {err.error_code}")
```
---

### MarketData Exception Class

```python
class MarketDataError(Exception):
    def __init__(
        self,
        message: str,
        error_code: str,
        provider: str | None = None,
        provider_status_code: int | None = None,
        retryable: bool = False,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.provider = provider
        self.provider_status_code = provider_status_code
        self.retryable = retryable
```

This class is located in:  src/mi_sdk/services/exceptions.py

When Calling an provider (eg. FMP provider),  you would do following:
```python
try:
    return fmp_provider.get_company_profile(symbol)

except ProviderError as exc:
    raise MarketDataError(
        message=exc.message,
        error_code=exc.error_code,
        provider=exc.provider,
        provider_status_code=exc.status_code,
        retryable=exc.retryable,
    ) from exc
```

### REST API Translates SDK Exception to HTTP Response

This is where the HTTP semantics come in.

With the FASTAPI, we would do the following:

```python
@app.exception_handler(MarketDataError)
async def market_data_error_handler(
    request: Request,
    exc: MarketDataError,
):
    status_code = map_error_to_http_status(exc.error_code)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "provider": exc.provider,
                "retryable": exc.retryable,
            }
        },
    )
```
The mapping of error code to status code is done in following method
```python
def map_error_to_http_status(error_code: str) -> int:
    return {
        "BAD_REQUEST": 400,
        "INVALID_API_KEY": 401,
        "FORBIDDEN_PLAN_LIMIT": 403,
        "SYMBOL_NOT_FOUND": 404,
        "RATE_LIMIT_EXCEEDED": 429,
        "PROVIDER_UNAUTHORIZED": 502,
        "PROVIDER_TIMEOUT": 504,
        "PROVIDER_UNAVAILABLE": 503,
        "PROVIDER_ERROR": 502,
    }.get(error_code, 500)
```

---

### Below is what SDK would do using the Company SDK as an example

The SDK catches a Provider error, maps to a MarketData Error and raises
a MarketData Exception so I can be handled by the API.

```python
from providers.common.exceptions import ProviderError
from exceptions import MarketDataError

class CompanyService:

    def get_profile(self, symbol: str):

        try:
            return self.provider.get_company_profile(symbol)

        except ProviderError as exc:
            raise MarketDataError(
                message=exc.message,
                error_code=exc.error_code,
                provider=exc.provider,
                provider_status_code=exc.status_code,
                retryable=exc.retryable,
            ) from exc
```

The REST layer only knows about SDK exceptions, which are MarketData errors, hence it would the following:
```python
from market_insights.sdk.exceptions import MarketDataError

@app.exception_handler(MarketDataError)
async def market_data_error_handler(
    request: Request,
    exc: MarketDataError,
):

```

The REST layer should not import ProviderError, and the FMP provider should not import MarketDataError.

----

### How to extend Exception Hierarchy for Provider specific errors in the future, as needed.

Below is example of extending the class hierarchy for 
provider-specific errors. You can create subclasses for each provider 
to handle their specific error codes and messages. 

```python
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
        error_code="PROVIDER_RATE_LIMIT_EXCEEDED",
        status_code=status_code,
        retryable=True,
    )
```

### How to extend Exception Hierarchy for the SDK specific errors in the future, as needed.

```python
class MarketDataError(Exception):
    ...

class MarketDataRateLimitError(MarketDataError):

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        provider_status_code: int | None = None,
    ):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            provider=provider,
            provider_status_code=provider_status_code,
            retryable=True,
        )
```

Now your SDK translates one abstraction into another:

```python
try:
    return self.provider.get_company_profile(symbol)

except ProviderRateLimitError as exc:
    raise MarketDataRateLimitError(
        message=exc.message,
        provider=exc.provider,
        provider_status_code=exc.status_code,
    ) from exc
```

And your REST API can specifically handle it:

```python
@app.exception_handler(MarketDataRateLimitError)
async def rate_limit_error_handler(
    request: Request,
    exc: MarketDataRateLimitError,
):
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "retryable": exc.retryable,
            }
        },
    )
```
### Below is the complete flow

![Error Flow](ErrorFlow.png)

Understand that if FMP returns a 429 error ("Too many requests"), does it makes sense for REST API to return same error to client. 
Perhaps not, because it is a limitation that you as the  MarketData Provider encountered with FMP. The client can misinterpret this as they exceeded number of requests.

In this situation, the MI client hasn't necessarily done anything wrong; your downstream FMP dependency is rate-limited.

I would consider translating the 429 error to a 503 error message something like "Market data is temporarily unavailable."

```json
{
  "error": {
    "code": "MARKET_DATA_RATE_LIMITED",
    "message": "Market data is temporarily unavailable.",
    "retryable": true
  }
}
```
Internally, your logs could retain:
```code
provider = FMP
provider_status_code = 429
```
without exposing FMP implementation details to consumers.

That distinction will become especially valuable if MI eventually uses multiple providers, because your REST API contract remains stable regardless of whether the underlying failure came from FMP, Yahoo, Polygon, or another market-data provider.


