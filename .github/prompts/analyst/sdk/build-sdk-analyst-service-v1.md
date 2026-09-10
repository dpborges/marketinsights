Build Analyst SDK service

**Role and Objective**

You are a Python SDK developer.  

- Create a analyst service SDK in a separate file called analyst_service.py. 
- In the analyst_service.py file, create a class called AnalystService. 
- In the AnalystService class, create method get_consensus() that calls the get_analyst_consensus method in the FMP adapter file fmp_analyst.
  - Inputs: A stock symbol or list of stock symbols, upto 10 symbols maximum.
  - Response: Will return the analyst consensus JSON from the fmp_analyst provider. 
- Create a method get_targets() that calls the get_analyst_targets method in the FMP adapter file fmp_analyst.py.  
  - Inputs: A stock symbol or list of stock symbols, upto 10 symbols maximum.
  - Response: Will return the analyst targets JSON from the fmp_analyst provider. 
- Create a method get_overall_recommendation(). See the Business logic section on how to assign the weights and calculate the over recommendation. 
  - Inputs: analyst consensus JSON returned from the fmp_analyst provider
  - Response: returns a string with an overall recommendation of strongBuy, buy, hold, sell, or strongSell. This recommendation is assigned to the consenses.recommendation property.
  

**Context:**
- Architecture:       	docs/sdk-architecture.md
- SDK Design:        	  docs/sdk-architecture.md
- Exception Handling:	docs/exception-handling.md
- SDK Services Directory  src/mi_sdk/services
- FMP providers Directory  src/mi_sdk/providers/fmp
- FMP analyst provider  fmp_analyst.py 


**Constraints:**
- Must follow .github/copilot-instructions.md
- Must not expose provider-specific logic in the SDK service

**Sample JSON response for get_consensus**
```json
{
  "consensus": [
    {
      "symbol": "NVDA",
      "strongBuy": 2,
      "buy": 58,
      "hold": 16,
      "sell": 3,
      "strongSell": 0,
      "recommendation": "buy"
    },
    {
      "symbol": "AAPL",
      "strongBuy": 2,
      "buy": 58,
      "hold": 16,
      "sell": 3,
      "strongSell": 0,
      "recommendation": "buy"
    }
  ],
  “errors”: [
	  <capture errors/exceptions here>
  ]
}
```

**Sample JSON response for get_targets**
```json
{
  "priceTargets": [
    {
      "symbol": "NVDA",
      "high": 400.0,
      "low": 245.0,
      "median": 360.0,
      "consensus": 339.35
    },
    {
      "symbol": "AAPL",
      "priceTarget": {
        "high": 400.0,
        "low": 245.0,
        "median": 360.0,
        "consensus": 339.35
      }
    }
  ],
  “errors”: [
	  <this will show the errors that were raised fmp_analyst adapter>
  ]
}
```

**Business Logic**

Create a separate method that uses a weighted average to combine all analsyt ratings into the "recommendation" label.
This accounts for both the number of analysts and the strength of their recommendations.

Assign these weights:

| Rating | Weight 
| --- | --- |
| buy	 | 4   |
| hold |	3  |
| sell |	2  |
| strongSell |	1 |

```
Calculate score as follows:

score = (
    strongBuy × 5 +
    buy × 4 +
    hold × 3 +
    sell × 2 +
    strongSell × 1
) / totalAnalysts
```

Map the score to a recommendation using these proposed thresholds:

| Score | Recommendation |
| --- | --- |
| 4.5–5.0            | strongBuy  |
| 3.5–less than 4.5  | buy        |
| 2.5–less than 3.5  | hold       |
| 1.5–less than 2.5  | sell       |
| 0.0–less than 1.5  | strongSell |

```
Here is an example conensus

{"symbol": "AAPL",
      "strongBuy": 2,
      "buy": 58,
      "hold": 16,
      "sell": 3,
      "strongSell": 0
}

This is the calculation

Total analysts = 2 + 58 + 16 + 3 + 0 = 79

Score = (2×5 + 58×4 + 16×3 + 3×2 + 0×1) / 79
      = 296 / 79
      ≈ 3.747

Recommendation = buy
```

**Validation Logic**
If more that 10 symbols are passed to either method, raise an error "exceeded maximum of 10 symbols per request".

**Exceptions**
If an exception is raised by the underlying adapter, they should be captured in the errors property in the above JSON structure.

**Implementation Details**
Since the methods in the fmp_analyst.py provider only support a single symbol parameter, in this SDK implement the ability to accept multiple symbols and call the respective fmp_analyst adapter method for each symbol in parallel. Wait until all method calls are completed for each symbol, get the overall recommendation for each symbo, set the consensus.recommendation property and return response all at once using the JSON response provided in the Sample JSON response section above. If a call failed for one or two symbols , return the others and capture the error for the given symbols in the error property. 


**Testing**

- Create a separate test file “test_analyst_service.py” in the SDK Test directory. 
- Include four tests. 
  - One to handle get_consensus for NVDA
  - One to handle get_consensus for NVDA,META,AAPL,IBM
  - One to handle get_targets for NVDA
  - One to handle get_targets for NVDA,META,AAPL,IBM
- Add a docstring on top of the file with the syntax for running the test.







