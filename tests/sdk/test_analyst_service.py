"""Run: .venv/Scripts/python.exe -m pytest tests/sdk/test_analyst_service.py"""

import asyncio
from typing import Any
from unittest.mock import AsyncMock

import pytest

from mi_sdk.domain.exceptions import DataValidationError, RateLimitError
from mi_sdk.interfaces.adapters import AnalystAdapter
from mi_sdk.services import AnalystService

COUNTS = {"strongBuy": 2, "buy": 58, "hold": 16, "sell": 3, "strongSell": 0}
TARGETS = {"high": 400.0, "low": 245.0, "median": 360.0, "consensus": 339.35}
SYMBOLS = ["NVDA", "META", "AAPL", "IBM"]


@pytest.fixture
def adapter() -> AsyncMock:
    source = AsyncMock(spec=AnalystAdapter)
    source.get_analyst_consensus.side_effect = lambda symbol: {
        "symbol": symbol,
        "analystConsensus": dict(COUNTS),
    }
    source.get_analyst_targets.side_effect = lambda symbol: {
        "symbol": symbol,
        "priceTarget": dict(TARGETS),
    }
    return source


async def test_get_consensus_nvda(adapter: AsyncMock) -> None:
    result = await AnalystService(adapter).get_consensus("NVDA")
    assert result == {
        "consensus": [{"symbol": "NVDA", **COUNTS, "recommendation": "buy"}],
        "errors": [],
    }
    adapter.get_analyst_consensus.assert_awaited_once_with("NVDA")


async def test_get_consensus_multiple(adapter: AsyncMock) -> None:
    result = await AnalystService(adapter).get_consensus(SYMBOLS)
    assert result == {
        "consensus": [{"symbol": symbol, **COUNTS, "recommendation": "buy"} for symbol in SYMBOLS],
        "errors": [],
    }
    assert adapter.get_analyst_consensus.await_count == 4


async def test_get_targets_nvda(adapter: AsyncMock) -> None:
    result = await AnalystService(adapter).get_targets("NVDA")
    assert result == {"priceTargets": [{"symbol": "NVDA", **TARGETS}], "errors": []}
    adapter.get_analyst_targets.assert_awaited_once_with("NVDA")


async def test_get_targets_multiple(adapter: AsyncMock) -> None:
    result = await AnalystService(adapter).get_targets(SYMBOLS)
    assert result == {
        "priceTargets": [{"symbol": symbol, **TARGETS} for symbol in SYMBOLS],
        "errors": [],
    }
    assert adapter.get_analyst_targets.await_count == 4


@pytest.mark.parametrize(
    "method,key,envelope",
    [
        ("get_consensus", "consensus", "analystConsensus"),
        ("get_targets", "priceTargets", "priceTarget"),
    ],
)
async def test_parallel_partial_failure(
    adapter: AsyncMock, method: str, key: str, envelope: str
) -> None:
    started: list[str] = []
    ready = asyncio.Event()

    async def fetch(symbol: str) -> dict[str, Any]:
        started.append(symbol)
        if len(started) == 4:
            ready.set()
        await asyncio.wait_for(ready.wait(), timeout=2)
        if symbol == "META":
            raise RateLimitError("Rate limit exceeded.")
        return {"symbol": symbol, envelope: COUNTS if key == "consensus" else TARGETS}

    getattr(
        adapter, "get_analyst_consensus" if key == "consensus" else "get_analyst_targets"
    ).side_effect = fetch
    result = await getattr(AnalystService(adapter), method)(SYMBOLS)
    assert [row["symbol"] for row in result[key]] == ["NVDA", "AAPL", "IBM"]
    assert result["errors"] == [
        {"symbol": "META", "code": "RateLimitError", "message": "Rate limit exceeded."}
    ]


@pytest.mark.parametrize("method", ["get_consensus", "get_targets"])
async def test_symbol_limit(adapter: AsyncMock, method: str) -> None:
    service = AnalystService(adapter)
    with pytest.raises(DataValidationError, match="^exceeded maximum of 10 symbols per request$"):
        await getattr(service, method)(["NVDA"] * 11)
    adapter.get_analyst_consensus.assert_not_awaited()
    adapter.get_analyst_targets.assert_not_awaited()
    result = await getattr(service, method)(["NVDA"] * 10)
    assert result["errors"] == []
    assert len(result["consensus" if method == "get_consensus" else "priceTargets"]) == 10


@pytest.mark.parametrize(
    "counts,label",
    [
        ((1, 0, 0, 0, 0), "strongBuy"),
        ((1, 1, 0, 0, 0), "strongBuy"),
        ((0, 1, 1, 0, 0), "buy"),
        ((0, 0, 1, 1, 0), "hold"),
        ((0, 0, 0, 1, 1), "sell"),
        ((0, 0, 0, 0, 1), "strongSell"),
    ],
)
def test_recommendation_boundaries(adapter: AsyncMock, counts: tuple[int, ...], label: str) -> None:
    service = AnalystService(adapter)
    ratings = dict(zip(COUNTS, counts, strict=True))
    assert service.get_overall_recommendation(ratings) == label
    assert service.get_overall_recommendation({"analystConsensus": ratings}) == label


@pytest.mark.parametrize("count", [0, -1, True, 0.5, float("nan"), float("inf"), None])
def test_invalid_ratings(adapter: AsyncMock, count: Any) -> None:
    ratings = dict.fromkeys(COUNTS, 0)
    ratings["buy"] = count
    with pytest.raises(DataValidationError):
        AnalystService(adapter).get_overall_recommendation(ratings)


@pytest.mark.parametrize("method", ["get_consensus", "get_targets"])
@pytest.mark.parametrize("symbols", [[], "", "NVDA,META", [None], ["NV DA"], None])
async def test_invalid_symbols(adapter: AsyncMock, method: str, symbols: Any) -> None:
    with pytest.raises(DataValidationError):
        await getattr(AnalystService(adapter), method)(symbols)
    adapter.get_analyst_consensus.assert_not_awaited()
    adapter.get_analyst_targets.assert_not_awaited()
