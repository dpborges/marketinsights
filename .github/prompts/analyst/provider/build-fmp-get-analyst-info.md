Analyst Adapter Prompt

**Role and Objective**
You are a Python Developer.
Create a new fmp adapter file called fmp_analyst.py. In this file create a method  called get_analyst_consensus and another method called get_analyst_targets.

**Context: **
- Architecture: 		docs/sdk-architecture.md
- SDK Design: 		docs/sdk/architecture.md
- Exception Handling:	docs/exception-handling.md

In each method add a comment section describing each method
Input: stock symbol
returns: json structure 

Below is an example method signature  for the get_analyst_consensus.
```Python
get_analyst_consensus( 
     symbol    
 ) 
```

Below is sample json response for get_analyst_consensus method
```json
{
  "symbol": "NVDA",
  "analystConsensus": {
    "strongBuy": 12,
    "buy": 28,
    "hold": 7,
    "sell": 1,
    "strongSell": 0
  }
}
```

Below is an example method signature for get_analyst_targets method
```python
get_analyst_targets( 
     symbol    
 ) 
 ```

Below is sample json response for get_analyst_targets method
```python
{
  "symbol": "NVDA",
  "priceTarget": {
    "high": 250.00,
    "low": 140.00,
    "median": 205.00,
    "consensus": 207.35
  }
}
```

Use API KEY found in the .env file. The property name is MARKET_FMP_API_KEY

Constraints:
- Must follow .github/copilot-instructions.md
- Must not expose provider-specific logic in the SDK service

After creating the required methods, create a separate file called fmp_analyst_run.py. Structure the file so I can execute and run analyst requests from the command line. If I provide no parameters, it should prompt me with a list of  available methods and display the required parameters. When I enter the method name and the parameter(s) it executes that method and writes responses or exceptions to standard output. 

On top of the fmp_analyst.py file, add a comment that provides the exact syntax for running a fmp_analyst.py adapter fromm command line.




