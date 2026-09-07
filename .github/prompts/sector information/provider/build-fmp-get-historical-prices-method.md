Historical Pricing Prompt

NOTE: This same method is used to get pricing for stocks and SPDR ETFs

Context: 
Architecture: 		docs/sdk-architecture.md
SDK Design: 		docs/sdk-architecture.md
Exception Handling:	docs/exception-handling.md


You are a Python Developer.
Create a totally new fmp_adapter.py file called fmp_adapter_v2 along with its own FMPAdapter class.  Create a new FMPAdapter  method called: get_historical_prices

In the method add comment section with the following:
Description: Returns historical pricing for all SPDR Sector ETFS, including the SPY. The SPY will be used by the SDK layer to calculate relative strength for each of the sectors.
Inputs: list of stock symbols,  as_of_date, lookback_periods.
returns: json structure with historical pricing for SYMBOLS provided  for the given date range.


Below is an example method signature for a 1 day lookback_ period. FMP automatically calculates the previous trading date. If as_of_date falls on a Monday, FMP will return the previous Friday’’s adjusted close price as the lookback price.

get_historical_prices( 
     symbols, 
     as_of_date=<YYYY-MM-DD>
     lookback_periods=<Whole Number>
 ) 

Below is sample response for 1 day look back period

{ 
  "provider": "FMP", 
   "prices": [ 
       { "symbol": "XLK", 
         "current":     { "date": "2026-07-16", "adjustedClose": 245.18 }, 
         "lookback":  { "date": "2026-07-15", "adjustedClose": 242.50 } 
      } 
   ] 
} 

Use API KEY found in the .env file. The property name is MARKET_FMP_API_KEY

Constraints:
- Must follow .github/copilot-instructions.md
- Must not expose provider-specific logic in the SDK service

  
After creating the required methods in the FMPAdapter, update the separate file called fmp_adapter_run.py. Update it in such a way that when I  run it from the command line with no parameters it should prompt me for what FMP service I would like to run (while displaying a list of  available services(aka methods)). When I enter the method name, it should prompt me for parameters while also displaying an example of the parameters I need to enter next. After entering the parameters, it writes responses or exceptions to standard output. 

Before the line where it defines the SERVICE METHODS in the fmp_adapter_run.py file, add a comment that provides the exact syntax for running a FMPAdapter service/method by invoking the FMPAdapterRun.




