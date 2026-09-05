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
Test directory:  tests/test_sectory_summary_service.py


You are a Python SDK developer.  
I would like to keep the JSON structure as is but  introduce two additional parameters to the sector summary_service.py SDK
sort_by:  where values can be  either “performance” or “relative_strength”  
sort_direction: where values are  either “asc” or “desc”  

When change is completed, the Sector Summary Service Implementation should accept four parameters:
a list of SPDR ETF Symbols, 
a list of periodCodes, 
sort_by  
sort_direction 

If no parameters are provided, the default should be a list of all the SPDR ETFS with a 2W period code, sort_by “relative_strength”  and sort_direction is “desc”.

Update the “test_sector_summary_service.py” file in the test directory  with the new parameters and update  comment on top with syntax for running script, as needed.

Run pytest after changes are completed to confirm changes were successful.
