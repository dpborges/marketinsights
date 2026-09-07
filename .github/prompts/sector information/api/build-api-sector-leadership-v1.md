**Build API Sector Leadership Service**

**Context:**
- Standards: 		.github/copilot-instructions.md
- Architecture:		docs/mi_api/architecture.md
- SDK Design:         	docs/sdk/architecture.md
- SDK Directory:	src/mi_sdk
- API Directory:  src/mi_api
- Exception Handling: 	docs/exception-handling.md

**Role and description of development task**

You are a Python FastAPI developer.  Create a sector leadership API  in the sector.py  router file within the API directory, which is used specifically for sector related end-points. 

This API will make use of the sector leadship SDK service found in the SDK directory. 

The sector leadership SDK accepts two parameters:

**Periods**
- The following are supported periodCodes:
  - 1D (for today)
  - 2W, 1M, 3M  (for 2 week, 1 month, and 3 month)
  - 6M, YTD, 1Y, 3Y, 5Y (translates to  6m, Year to date, 1 year, 3 year and 5 year)

**top_n**
  - where top_n can be top 3 or top 5 sector leaders

The SDK service to be used for this API is called: sector_leadership_service.py
…and can be found in the SDK directory:   src/mi_sdk/services

**Sample URL Requests**

Endpoint1: /api/v1/sector/leadership?periods=2W,1M,3M&top_n=3

When this endpoint is called, it calls the sector_leadership_service.py SDK and returns the top 3 sectors using the periods provided

Endpoint2: /api/v1/sector/leadership?periods=2W,1M,3M&top_n=5

When this endpoint is called, it calls the sector_leadership_service.py SDK and returns the top 5 sectors using the periods provided

Endpoint2: /api/v1/sector/leadership?&top_n=5

When this endpoint is called, it will be default to the following periods: periods=2W,1M,3M and calls the sector_leadership_service.py SDK and returns the top 5 sectors using the default periods.

Endpoint2: /api/v1/sector/leadership?&top_n=3

When this endpoint is called, it will be default to the following periods: periods=2W,1M,3M and calls the sector_leadership_service.py SDK and returns the top 5 sectors using the default periods.

**Json Stucture that will be returned**

The JSON structure below will be returned by the sector_leadership SDK service which in turn will be returned by the sector_leadership API we are building here. 

```json
{
  "benchmark": "SPY",
  "asOfDate": "2026-09-06",
  "requestedSectorCount": 11,
  "successfulSectorCount": 11,
  "failedSectorCount": 0,
  “sectors”: [
      {
  "symbol": "XLK",
  "sector": "Technology",
   "relativeStrengthRank": 1,
   "returnRank": 3,
   "outperformedBenchmark": true
               "interpretation": {
   "status": "strong_established_leader",
    "supports_entry": true,
    "reason": "Sector ranks in the top 5 across 2W, 1M, and 3M."
  	    }
      },
      {
  "symbol": "XLI",
  "sector": "Industrials",
   "relativeStrengthRank": 2,
   "returnRank": 3,
   "outperformedBenchmark": true
               "interpretation": {
   "status": "strong_established_leader",
    "supports_entry": true,
    "reason": "Sector ranks in the top 5 across 2W, 1M, and 3M."
  	    }
      },
     {
	< 3rd entry here structured same as 1st and second entry>
      },
      {
	< if using top_n=5, the 4th and 5th entry will be structured same as 1st and second entry>
      }
],
“errors”: [
	<this will show the errors that were raised as part of the SDK call to sector summary>
]
}
```
**Implementation recommendations:**

If an error or errors are raised by the underlying service_leadership sdk, they should be captured in the errors property in the above JSON structure.


***Recommended behavior:***

- If periods are omitted, default to the following 3 periods 2W, 1M, and 3M.
- The top_n parameter accepts the value 3 or 5. If something else other than 3 or 5 is entered, raise Error: "Invald top_n value. Only 3 and 5 are supported"

  
**Testing:**

Add docstring on the top of src/mi_api/routers/sector.py documenting the two services available: sector_summary and sector_leadership

Create test harness in the tests/api folder

Update the following /docs/mi_api/testing-documentation.md with instructions on how to run the test harness for sector_leadership.  Provide exact command line syntax.

