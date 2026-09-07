Build API Sector Summary

You are a Python FASTAPI developer.  
I would like to  introduce two additional parameters to the sector summary API:
sort_by:  where values can be  either “performance” or “relative_strength”  
sort_direction: where values are  either “asc” or “desc”  

Keep JSON response structure “as is”.

When change is completed, the Sector Summary API should accept four parameters:
a list of SPDR ETF Symbols, 
a list of periodCodes, 
sort_by  
sort_direction 

Here  is a  sample endpoint url that returns all SPDR symbols for a 2 week period sorted by relative strength and sort direction is set to descending.
Endpoint: /api/v1/sector/summary?periods=2W&sort_by=relative_strength&sort_direction=desc

Context: 
API directory:  src/mi_api/routers
API sector router file:  sectory.py

I am submitting the original prompt used to create the Sector Summary API.  The start  of the original prompt is  marked with <START OF Sector Summary v1 prompt>. 
The  end of the original prompt is marked with  <END OF Sector Summary v1 prompt>.

You can use previous context and instructions for the original prompt as reference.

<START OF Sector Summary v1 prompt>
Context:
- FastAPI standards: .github/copilot-instructions.md
- Architecture:         docs/mi_api/architecture.md
- SDK Design:         docs/sdk/architecture.md
- Exception Handling: docs/exception-handling.md

You are a Python SDK developer.  Create a sector summary API in a separate router file that will be used specifically for sector related end-points. 

This API will make use of the Sector summary SDK. The sector summary SDK accepts 2 parameters:
Periods 
Use the following as supported periodCodes:
1D (for today)
2W, 1M, 3M  (for 2 week, 1 month, and 3 month)
6M, YTD, 1Y, 3Y, 5Y (translates to  6m, Year to date, 1 year, 3 year and 5 year)
Symbols
            For example XLB,XLC,XLE,XLF,XLI,XLK,XLP,XLRE,XLU,XLV,XLY

SDK service is called: sector_summary_service.py
…and can be found in the SDK directory:   src/mi_sdk/services

Below is a sample of the variation of endpoints that should be supported.

Endpoint1:  /api/v1/sector/summary
When this endpoint is called, call the sector_summary_service.py SDK  with no parameters. When no parameters are provided, the default behavior will be to return a sector summary for all SPDR ETFs for that last 2 week period.

Endpoint2: /api/v1/sector/summary?periods=1D&symbols=XLK
When this endpoint is called, it callsl the sector_summary_service.py SDK and returns sector summary for one symbol and one period

Endpoint3: /api/v1/sector/summary?periods=2W,1M,3M
When this endpoint is called, it calls the sector_summary_service.py SDK and returns sector summary for multiple periods and all symbols

Endpoint4: /api/v1/sector/summary?symbols=XLF,XLK,XLV
When this endpoint is called, it calls the sector_summary_service.py SDK and returns sector summary for select symbols and the default period of 2W (two weeks)

Endpoint5: /api/v1/sector/summary?symbols=XLF,XLK,XLV
When this endpoint is called, it calls the sector_summary_service.py SDK and returns sector summary for select symbols and the default period of 2W (two weeks)

Implementation recommendations:
Accept values case-insensitively but return canonical uppercase codes.
Remove duplicates while preserving requested order.
Use omission to mean “all symbols”; an explicit symbols=all is unnecessary.
Return 422 Unprocessable Entity for unsupported periods or symbols.
Clearly define 1D: if it means the latest trading session rather than the current calendar day, describe it as “one trading day” to avoid weekend and holiday ambiguity.
Keep the plural parameter names because both accept lists.
A useful validation-error response would be:
{
  "error": {
    "code": "INVALID_QUERY_PARAMETER",
    "message": "Unsupported period code: 4M",
    "parameter": "periods",
    "allowedValues": ["1D", "2W", "1M", "3M", "6M", "YTD", "1Y", "3Y", "5Y"]
  }
}
Recommended behavior:
Split values on commas.
Trim whitespace and normalize to uppercase.
Reject empty items, unsupported values, and ideally duplicates.
When periods is omitted, use the existing 2W default.
When symbols is omitted, use all supported sector symbols.
Document each parameter as a comma-separated string in OpenAPI.
I understand that FastAPI does not automatically parse comma-separated query values into list[str]; the endpoint must split and validate them. Given this is a small amount of code, I believe shorting it instead of repeated query parameters makes it more readable, and justifies using the additional code.

Create test harness in the tests/api folder

Update the following /docs/mi_api/testing-documentation.md with instructions on how to run the test harness. Provide exact command line syntax.
<END OF Sector Summary v1 prompt>.

