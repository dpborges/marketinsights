Build Company API

## Preamble

Before moving forward stop here and read the **pre-execution review** document located in this file: 
```code
.github/prompts/_prompt_templates/pre-execution-basic-review.md 
```
and then we can proceed with the prompt below as directed. 

## Role and Objective

You are a Python FASTAPI developer.  Create a Company API in a separate router file that will be used specifically for Company related end-points. This API will make use of the CompanyService SDK. 

Context:
- FastAPI standards: .github/copilot-instructions.md
- Architecture:       .github/copilot-instructions.md
- SDK Design:         .github/copilot-instructions.md
- SDK Directory:	    src/mi_sdk
- API Directory:      src/mi_api
- SDK Service:        src/mi_sdk/services/company_service.py
- Exception Handling: .github/prompts/exception_management/exception_management.md

### Implementation guidelines
The Company API should expose the following SDK methods:
  - get_summary
  - get_profile

Both methods in the SDK take a list of stock symbols as parameters.

The SDK service to be used for this API is called: company_service.py 
and can be found in the SDK directory:   src/mi_sdk/services

### Sample URL GET Requests

- Endpoint1: /api/v1/company/profile?symbols=META
- Endpoint2: /api/v1/company/profile?symbols=META,MSFT

- Endpoint3: /api/v1/company/summary?symbols=META
- Endpoint4: /api/v1/company/summary?symbols=AAPL,META,APPL

When endpoint /api/v1/company/profile is called,
it invokes the get_profile() method on the company_service.py SDK and 
When endpoint /api/v1/company/summary is called,
it invokes the get_summary() method on the company_service.py SDK.

Both methods return the JSON object from each of their respective methods "as-is".
Both methods should understand how to map exceptions from the SDK to the HTTP response using guidance in the Exceptions section of this prompt.


### Exceptions
Have the Company API employ the Exception handling pattern for API's, that is documented in file 
```code .github/prompts/exception_management/exception_management.md.```

### Validations

- If symbols are omitted, return error message, "No symbols provided" and set  appropriate HTTP status code 400.
- If more than 10 symbols are submitted raise return error: "10 symbol request limit exceeded" with HTTP status code 400.

  
## Testing

Document the endpoints with a brief description on top of the src/mi_api/routers/company.py file.

Create test harness in the tests/api folder

Update the following  file /docs/mi_api/testing-documentation.md with instructions on how to run the test harness for the Company API. 

Add the new api to the docs url http://localhost:8000/docs.



