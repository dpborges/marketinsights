Build Company API

## Preamble

Before moving forward stop here and read the **pre-execution review** document located in this file: 
```code
.github/prompts/_prompt_templates/pre-execution-basic-review.md 
```
and then we can proceed with the prompt below as directed. 

## Role and Objective

You are a Python FASTAPI developer. Create a Calculation API in a separate router file that will be used specifically for Calculation related end-points. This API will make use of the get_stop_loss() method in the calculation service SDK to expose it via the Calcuation API. 

Context:
- FastAPI standards: .github/copilot-instructions.md
- Architecture:       .github/copilot-instructions.md
- SDK Design:         .github/copilot-instructions.md
- SDK Directory:	    src/mi_sdk
- API Directory:      src/mi_api
- SDK Service:        src/mi_sdk/services/calculation_service.py
- Exception Handling: .github/prompts/exception_management/exception_management.md

### Implementation guidelines
The Calculation API should expose the following SDK method(s):
  - get_stop_loss
  
The API will accept two paramters
- a list of stock symbols 
- a list of horizons : SHORT, MEDIUM, LONG

The SDK service to be used for this API is called: calculation_service.py 
and can be found in the SDK directory:   src/mi_sdk/services

### Sample URL GET Requests

- Endpoint1: /api/v1/calculation/stop-loss?symbols=META&horizons=SHORT,MEDIUM
- Endpoint2: /api/v1/calculation/stop-loss?symbols=IBM&horizons=short,medium

- Endpoint3: /api/v1/calculation/stop-loss?symbols=AAPL&horizons=short
- Endpoint4: /api/v1/calculation/stop-loss?symbols=,META,APPL&horizons=SHORT,medium,LONG

When endpoint /api/v1/calculation/stop-loss is called,
it invokes the get_stop_loss() method on the calculation_service.py SDK.

The API returns the JSON object from the respective get_stop_loss method "as-is".
The API should understand how to map exceptions from the SDK to the HTTP response using guidance in the Exceptions section of this prompt.

### Exceptions
Have the Calculation API employ the Exception handling pattern for API's, that is documented in file 
```code .github/prompts/exception_management/exception_management.md.```

### Validations

- If the symbols parameter or symbols list are omitted, return HTTP status code 400 (BAD REQUEST) with message  "No symbols provided".
- If more than 10 symbols are submitted raise return error: "10 symbol request limit exceeded" with HTTP status code 400.
- If horizons parameter is omitted, default to horizons=SHORT
- If the horizons parameter is provided with emtpy horizons list, return HTTP status code 400 (BAD REQUEST) with message  "No horizons provided".
- If horizons parameter is provided with case in-senstive values other than SHORT, MEDIUM, or LONG, return HTTPS status 400 with message "Invalid horizon value provided"

  
## Testing

Document the endpoints with a brief description on top of the src/mi_api/routers/calculation.py file.

Create test harness in the tests/api folder


## Documentation

Update the following  file /docs/mi_api/testing-documentation.md with instructions on how to run the test harness for the Calculation API. 

Add the new api to the docs url http://localhost:8000/docs.



