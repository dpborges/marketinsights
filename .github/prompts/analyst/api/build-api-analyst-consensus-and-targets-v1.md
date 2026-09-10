**Build Analyst API**

Review the prompt below and let me know if you have any questions, need clarifications, or find something that is incorrect or possibly mis-stated. If so, ask me to clarify it before executing the prompt. If everything is clear, feel free to execute the prompt.

**Role and description of development task**

You are a Python FastAPI developer.  Create an analyst API in a separate router file within the API directory.

**Context:**
- Standards: 		.github/copilot-instructions.md
- Architecture:		docs/mi_api/architecture.md
- SDK Design:         	docs/sdk/architecture.md
- SDK Directory:	src/mi_sdk
- API Directory:  src/mi_api
- SDK Analyst Service:    src/mi_sdk/services/analyst_service.py
- Exception Handling: 	docs/exception-handling.md


The SDK service to be used for this API is called: analyst_service.py 
and can be found in the SDK directory:   src/mi_sdk/services

Both the get_consensus method and get_targets method in the SDK take a list of stock symbols as parameters.

**Sample URL GET Requests**

Endpoint1: /api/v1/analyst/consensus?symbols=META
Endpoint2: /api/v1/analyst/consensus?symbols=AAPL,META,APPL

When these endpoints are called, it calls the get_consensus() method on the analyst_service.py SDK and it returns the JSON object back to client. The JSON object will contain consensus for either one symbol or all three.

Endpoint3: /api/v1/analyst/targets?symbols=AAPL
Endpoint4: /api/v1/analyst/targets?symbols=AAPL,META,APPL

When these endpoints are called, it calls the get_targets() method on the analyst_service.py SDK and it returns the JSON object back to client. The JSON object will contain consensus for either one symbol or all three.


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
      "high": 400.0,
      "low": 245.0,
      "median": 360.0,
      "consensus": 339.35
    }
  ],
  “errors”: [
	  <this will show the errors that were raised fmp_analyst adapter>
  ]
}
```

**Errors/Exceptions**
- Display the errors property in the JSON response only if there are errors. If there are no errors, do note show the errors property.


***Validations***

- If symbols are omitted, raise Error: No symbols provided and set  appropriate HTTP status code 400.
- If more than 10 symbols are submitted raise Error: 10 symbol request limit exceeded along with the setting the HTTP status code 400.

  
**Testing:**

Document the endpoints with a brief description on top of the src/mi_api/routers/analyst.py file.

Create test harness in the tests/api folder

Update the following  file /docs/mi_api/testing-documentation.md with instructions on how to run the test harness.  Provide exact command line syntax.

Add the new api to the docs url http://localhost:8000/docs.



