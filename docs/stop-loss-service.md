# Stop-loss calculation SDK

`CalculationService.get_stop_loss(symbols, horizons)` is asynchronous. It returns
JSON-compatible `companies`, `errors`, and `summary` dictionaries using the SDK's
existing batch policy. No additional dependencies or API route are required.

```python
from mi_sdk import SDKSettings, ServiceFactory

service = ServiceFactory(SDKSettings()).create_calculation_service()
result = await service.get_stop_loss(["AAPL", "IBM"], ["SHORT", "MEDIUM", "LONG"])
```

`currentPrice` is the `price` from `CompanyService.get_summary([symbol])`.
`CalculationService._get_current_price()` isolates this temporary dependency for
replacement with a future `CompanyService.get_current_price()` method. Historical
closes are used for ATR, never as a substitute for this quote.

Symbols are normalized and deduplicated before enforcing the ten-symbol limit.
Horizons are required, case-insensitive, and deduplicated in request order.
Invalid requests raise `MarketDataError` with `BAD_REQUEST` before data retrieval.

| Horizon | Calendar lookback | Bars | ATR period | Buffer | Swing window |
| --- | --- | --- | --- | --- | --- |
| SHORT | 6 months | Daily | 14 | 0.50 ATR | 2 |
| MEDIUM | 12 months | Daily | 20 | 0.75 ATR | 2 |
| LONG | 36 months | Weekly | 14 | 1.00 ATR | 2 |

One daily-history request per symbol spans the longest requested lookback. Each
horizon is calculated using its own calendar slice, so adding LONG does not
change SHORT. A single date is captured for the batch; tests can inject `today`.
The starting parameters have not been backtested.

## Calculation rules

1. Sort daily OHLCV by date. Reject duplicate/future dates, nonfinite or missing
   values, nonpositive prices, negative volume, and inconsistent OHLC ranges.
2. For LONG, aggregate Monday-based calendar weeks: first open, maximum high,
   minimum low, last close, and summed volume. Exclude the current week and any
   first week starting before the available daily slice. No exchange holiday
   calendar is used; missing sessions are not synthesized.
3. True range is `max(high-low, abs(high-previousClose), abs(low-previousClose))`.
   Seed ATR with the mean of N ranges having previous closes (N+1 bars), then use
   Wilder smoothing: `ATR = previousATR * (N-1)/N + TR/N`.
4. Confirm a swing low using W bars on both sides. The low must be no higher than
   any neighbor and lower than at least one on each side. A contiguous equal-low
   plateau requires W confirming bars outside its edges and counts once, at its
   final bar. Flat series and unconfirmed endpoints generate no swings.
5. Keep swings below current price. Sort by price and cluster with a maximum
   zone span of 0.5 ATR; do not chain together distant levels. Zone price is the
   mean of its swing prices, and touches is the number of confirmed swings.
6. Score each zone as `0.4*touchScore + 0.3*recencyScore + 0.3*reboundScore`:
   - `touchScore = min(touches/5, 1)`.
   - `recencyScore = latestTouchIndex/(barCount-1)`.
   - For each touch, take the highest high in its W following bars minus its
     low, divide by 2 ATR, and clamp to [0,1]. Rebound score is the mean of these
     values (zero if ATR is zero).
7. Select the highest-scoring zone that produces a stop strictly between zero
   and current price. Ties prefer the latest touch, then higher support price.
8. `stopLoss.price = support.price - ATR * bufferMultiplier` and
   `downsidePct = (currentPrice-stopLoss.price)/currentPrice * 100`.
   Preserve floating-point precision for downstream calculations.

Horizon awareness comes from lookback, bar timeframe, ATR period, and buffer.
Stops are not forced into a particular ordering across horizons.

## Configuration and errors

`StopLossSettings` reads `.env` and environment variables with `STOP_LOSS_` prefix.
For each of `SHORT`, `MEDIUM`, and `LONG`, supported suffixes are `ATR_PERIOD`,
`ATR_BUFFER`, and `SWING_WINDOW`; for example, `STOP_LOSS_LONG_SWING_WINDOW=2`.
Periods/windows must be positive integers; buffers must be finite and nonnegative.
Pass explicit settings to the constructor or `create_calculation_service(settings)`.

Each symbol succeeds only if every requested horizon succeeds. Insufficient bars
produce `INSUFFICIENT_HISTORY`; absent support or an invalid stop produces
`NO_VALID_SUPPORT`; malformed prices produce `INVALID_PRICE_DATA`. These errors
are nonretryable per-symbol results. Successful symbols remain in the batch.
All item failures return an empty companies list with populated errors and counts.
Operation-wide timeouts or unavailability raise retryable `MarketDataError`, as
in other SDK services. Provider details are not included in per-symbol errors.

Use prices supplied by the company SDK consistently; this service does not apply
additional split/dividend adjustments or check quote freshness. The calculation
is deterministic for the same data, settings, and date, rather than across live
market updates.
