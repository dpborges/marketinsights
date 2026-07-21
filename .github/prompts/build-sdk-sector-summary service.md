SDK Build Sector Summary Service

Context:
- Architecture:       	docs/sdk-architecture.md
- SDK Design:        	docs/sdk-architecture.md
- Exception Handling:	docs/exception-handling.md

Constraints:
- Must follow .github/copilot-instructions.md
- Must not expose provider-specific logic in the SDK service

Dependency: providers/fmp/smp_adapter.py get_historical_prices method
SDK directory:   src/mi_sdk/services

You are a Python SDK developer.  
Create a sector_summary service SDK, in a separate file called sector_summary_service.py,  that leverages the FMPAdapter get_historical_prices method to retrieve the current and the lookback prices for a given period,  for  all SPDR Sector ETF’s ( XLB,XLC,XLE,XLF,XLI,XLK,XLP,XLRE,XLU,XLV,XLY)  and the SPY benchmark.
It uses the price information, for the given period,  to calculate and provide a sector summary for each SPDR ETF that includes the return value and relative strength 

The SectorSummaryService Implementation should accept two parameters: a list of SPDR ETF Symbols and a list of periodCodes. If no parameters are provided, the default should be a list of all the SPDR ETFS and a single list item with the 2W period code.

On top of the sector_summary_service.py file add a comment section providing a  description of the service, the service parameters, and the outcome if  no parameters are provided.


Use the following as supported periodCodes: 
1D (for today)
2W, 1M, 3M  (for 2 week, 1 month, and 3 month)
6M, YTD, 1Y, 3Y, 5Y (translates to  6m, Year to date, 1 year, 3 year and 5 year)

Below is a default sample JSON response depicting JSON structure with only two SPDR ETFs, but the service is expected to return all SPDR ETFs, using this structure.

{
  "provider": "FMP",
  "status": "SUCCESS",
  "asOfDate": "2026-07-16",
  "period": {
    "periodCode": "2W",
    "requestedTradingDays": 10,
    "currentDate": "2026-07-16",
    "lookbackDate": "2026-07-02"
  },
  "benchmark": {
    "symbol": "SPY",
    "currentAdjustedClose": 681.42,
    "lookbackAdjustedClose": 660.25,
    "absoluteChange": 21.17,
    "returnPct": 3.2056
  },
  "requestedSectorCount": 11,
  "successfulSectorCount": 11,
  "failedSectorCount": 0,
  "sectors": [
    {
      "symbol": "XLK",
      "sectorCode": "TECHNOLOGY",
      "sectorName": "Technology",
      "current": {
        "date": "2026-07-16",
        "adjustedClose": 245.18
      },
      "lookback": {
        "date": "2026-07-02",
        "adjustedClose": 231.40
      },
      "performance": {
        "absoluteChange": 13.78,
        "returnPct": 5.9551
      },
      "relativeStrength": {
        "excessReturnPct": 2.7495,
        "outperformedBenchmark": true
      },
      "ranking": {
        "returnRank": 1,
        "relativeStrengthRank": 1
      }
    },
    {
      "symbol": "XLF",
      "sectorCode": "FINANCIALS",
      "sectorName": "Financials",
      "current": {
        "date": "2026-07-16",
        "adjustedClose": 53.75
      },
      "lookback": {
        "date": "2026-07-02",
        "adjustedClose": 52.40
      },
      "performance": {
        "absoluteChange": 1.35,
        "returnPct": 2.5763
      },
      "relativeStrength": {
        "excessReturnPct": -0.6293,
        "outperformedBenchmark": false
      },
      "ranking": {
        "returnRank": 7,
        "relativeStrengthRank": 7
      }
    }
    …..assume remaining SPDR tickers are shown
  ],
  "errors": []
}

The calculations would be: 

sectorReturnPct =  ((sectorCurrent - sectorLookback) / sectorLookback) × 100
benchmarkReturnPct =     ((spyCurrent - spyLookback) / spyLookback) × 100
excessReturnPct =   sectorReturnPct - benchmarkReturnPct

Sort the result  in ascending order by relativeStrengthRank.

For service to support a multiple period structure, for example 2W, 1M, 3M, etc., make periods an array,
Below is sample response for multiple period request

{
  "provider": "FMP",
  "status": "SUCCESS",
  "asOfDate": "2026-07-16",
  "benchmark": {
    "symbol": "SPY",
    "periods": [
      {
        "periodCode": "2W",
        "requestedTradingDays": 10,
        "currentDate": "2026-07-16",
        "lookbackDate": "2026-07-02",
        "performance": {
          "returnPct": 3.2056
        }
      },
      {
        "periodCode": "1M",
        "requestedTradingDays": 21,
        "currentDate": "2026-07-16",
        "lookbackDate": "2026-06-16",
        "performance": {
          "returnPct": 4.8512
        }
      },
      {
        "periodCode": "3M",
        "requestedTradingDays": 63,
        "currentDate": "2026-07-16",
        "lookbackDate": "2026-04-16",
        "performance": {
          "returnPct": 10.2268
        }
      }
    ]
  },
  "requestedSectorCount": 1,
  "successfulSectorCount": 1,
  "failedSectorCount": 0,
  "sectors": [
    {
      "symbol": "XLK",
      "sectorCode": "TECHNOLOGY",
      "sectorName": "Technology",
      "periods": [
        {
          "periodCode": "2W",
          "performance": {
            "returnPct": 5.9551
          },
          "relativeStrength": {
            "excessReturnPct": 2.7495,
            "outperformedBenchmark": true
          },
          "ranking": {
            "returnRank": 1,
            "relativeStrengthRank": 1
          }
        },
        {
          "periodCode": "1M",
          "performance": {
            "returnPct": 8.1041
          },
          "relativeStrength": {
            "excessReturnPct": 3.2529,
            "outperformedBenchmark": true
          },
          "ranking": {
            "returnRank": 1,
            "relativeStrengthRank": 1
          }
        },
        {
          "periodCode": "3M",
          "performance": {
            "returnPct": 16.9194
          },
          "relativeStrength": {
            "excessReturnPct": 6.6926,
            "outperformedBenchmark": true
          },
          "ranking": {
            "returnRank": 1,
            "relativeStrengthRank": 1
          }
        }
      ]
    }
  ],
  "errors": []
}







