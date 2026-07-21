"""Tests for FMP adapter"""

import os

import pytest
from unittest.mock import AsyncMock, Mock, patch

import httpx

from mi_sdk.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DataValidationError,
    ProviderUnavailableError,
    RateLimitError,
)
from mi_sdk.providers.fmp.fmp_adapter import FMPAdapter


class TestFMPAdapter:
    """Test cases for the FMP adapter."""

    @pytest.fixture
    def adapter(self) -> FMPAdapter:
        return FMPAdapter(api_key="test_key", timeout=30)

    @pytest.fixture
    def historical_payload(self) -> list[dict]:
        return [
            {"date": "2026-07-09", "adjClose": 100.0},
            {"date": "2026-07-10", "adjClose": 101.0},
            {"date": "2026-07-13", "adjClose": 102.0},
            {"date": "2026-07-14", "adjClose": 103.0},
            {"date": "2026-07-15", "adjClose": 104.0},
            {"date": "2026-07-16", "adjClose": 105.0},
        ]

    def test_get_historical_prices_success(self, adapter: FMPAdapter, historical_payload: list[dict]) -> None:
        with patch("mi_sdk.providers.fmp.fmp_adapter.httpx.Client") as mock_client_class:
            mock_response = Mock()
            mock_response.json.return_value = historical_payload
            mock_response.raise_for_status = Mock()

            mock_client = Mock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            result = adapter.get_historical_prices(["AAPL"], "2026-07-16", 5)

            assert result["provider"] == "FMP"
            assert len(result["prices"]) == 1
            assert result["prices"][0]["symbol"] == "AAPL"
            assert result["prices"][0]["current"]["adjustedClose"] == 105.0
            assert result["prices"][0]["lookback"]["adjustedClose"] == 100.0

    def test_get_historical_prices_invalid_date(self, adapter: FMPAdapter) -> None:
        with pytest.raises(DataValidationError, match="Invalid as_of_date"):
            adapter.get_historical_prices(["AAPL"], "07-16-2026", 5)

    def test_get_historical_prices_invalid_lookback(self, adapter: FMPAdapter) -> None:
        with pytest.raises(DataValidationError, match="lookback_periods must be a whole number"):
            adapter.get_historical_prices(["AAPL"], "2026-07-16", 0)

    def test_get_historical_prices_http_error_raises_provider_unavailable(self, adapter: FMPAdapter) -> None:
        with patch("mi_sdk.providers.fmp.fmp_adapter.httpx.Client") as mock_client_class:
            mock_response = Mock()
            request = httpx.Request("GET", "https://financialmodelingprep.com/stable/historical-price-eod/dividend-adjusted")
            response = httpx.Response(500, request=request, text="Server error")
            exc = httpx.HTTPStatusError("500 Server Error", request=request, response=response)
            mock_response.raise_for_status.side_effect = exc

            mock_client = Mock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            with pytest.raises(ProviderUnavailableError, match="Failed to fetch historical pricing"):
                adapter.get_historical_prices(["AAPL"], "2026-07-16", 5)

    def test_get_historical_prices_missing_data_returns_failed_response(self, adapter: FMPAdapter) -> None:
        with patch("mi_sdk.providers.fmp.fmp_adapter.httpx.Client") as mock_client_class:
            mock_historical_response = Mock()
            mock_historical_response.json.return_value = []
            mock_historical_response.raise_for_status = Mock()

            mock_quote_response = Mock()
            mock_quote_response.json.return_value = [{"symbol": "AAPL"}]
            mock_quote_response.raise_for_status = Mock()

            mock_client = Mock()
            mock_client.get.side_effect = [mock_historical_response, mock_quote_response]
            mock_client_class.return_value.__enter__.return_value = mock_client

            result = adapter.get_historical_prices(["AAPL"], "2026-07-16", 5)

            assert result["provider"] == "FMP"
            assert result["status"] == "FAILED"
            assert result["requestedSymbolCount"] == 1
            assert result["successfulSymbolCount"] == 0
            assert result["failedSymbolCount"] == 1
            assert result["errors"][0]["code"] == "NO_PRICE_DATA"
            assert result["errors"][0]["symbol"] == "AAPL"

    def test_get_historical_prices_invalid_symbol_returns_symbol_not_found(self, adapter: FMPAdapter) -> None:
        with patch("mi_sdk.providers.fmp.fmp_adapter.httpx.Client") as mock_client_class:
            mock_historical_response = Mock()
            mock_historical_response.json.return_value = []
            mock_historical_response.raise_for_status = Mock()

            mock_quote_response = Mock()
            mock_quote_response.json.return_value = []
            mock_quote_response.raise_for_status = Mock()

            mock_client = Mock()
            mock_client.get.side_effect = [mock_historical_response, mock_quote_response]
            mock_client_class.return_value.__enter__.return_value = mock_client

            result = adapter.get_historical_prices(["INVALID"], "2026-07-16", 5)

            assert result["provider"] == "FMP"
            assert result["status"] == "FAILED"
            assert result["requestedSymbolCount"] == 1
            assert result["successfulSymbolCount"] == 0
            assert result["failedSymbolCount"] == 1
            assert result["errors"][0]["code"] == "SYMBOL_NOT_FOUND"
            assert result["errors"][0]["symbol"] == "INVALID"

