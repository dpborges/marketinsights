Build <api-name> API

## Preamble

Before moving forward stop here and read the **pre-execution review** document located in this file: 
```code
.github/prompts/_prompt_templates/pre-execution-reviews/pre-execution-basic-review.md 
```
and then we can proceed with the prompt below as directed. 

## Role and Objective

You are a Python FASTAPI developer. Create a <api-name> API in a separate router file that will be used specifically for <api-name> related end-points. This API will make use of the <sdk-method-name-being-called> method in the <sdk-service-name> service SDK to expose it via the <api-name> API. 

**Context:**
- FastAPI standards:  .github/copilot-instructions.md
- Architecture:       .github/copilot-instructions.md
- SDK Design:         .github/copilot-instructions.md
- SDK Architecture:   docs/sdk/architecture.md
- SDK Directory:	    src/mi_sdk
- API Directory:      src/mi_api
- SDK Service:        src/mi_sdk/services/<sdk-service-name>_service.py
- Exception Handling: .github/prompts/exception_management/exception_management.md

### Implementation guidelines
The <api-name> API should expose the following SDK method(s):
  - <sdk-method-name-being-exposed>
  
The API will accept <number> parameters
- <parameter-name>: <parameter-description>; Sample values are: <sample-value(s)>

The SDK service to be used for this API is called: <sdk-service-name>_service.py 
and can be found in the SDK directory:   src/mi_sdk/services

The API returns the JSON object from the respective <sdk-method-name>() method "as-is".
The API should understand how to map exceptions from the SDK to the HTTP response using guidance in the Exceptions section of this prompt.

### Sample URL GET Requests

- Endpoint1: /api/v1/<resource-name>/<sub-resource-name>?<sample-query-string1>
- Endpoint2: /api/v1/<resource-name>/<sub-resource-name>?<sample-query-string2>

When endpoint /api/v1/<resource-name>/<sub-resource-name> is called,
it invokes the <sdk-method-name> method on the <sdk-service-name>_service.py SDK.

### Exceptions
Have the Calculation API employ the Exception handling pattern for API's, that is documented in file 
```code .github/prompts/exception_management/exception_management.md.```

### Validations and Defaults

The API will accept <number> parameters
- <parameter-name>: <parameter-description>; Sample values are: <sample-value(s)>
  
**Parameter Missing Errors**
- If the mandatory <parameter-name> parameter is omitted, return HTTP status code 400 (BAD REQUEST) with message  "Parameter <parameter-name> missing".

**Parameter Values Missing errors**
- If the <parameter-name> is provided with no values, return HTTP status code 400 (BAD REQUEST) with message  "No <parameter-name-values> provided".

**Defaults**
- If <parameter-name> parameter is omitted, default it to <parameter-name>=<default-value>

**Maximum value exceeded**
- If the value of <parameter-name> exceeds the max value of <the-max-value> return HTTP status code 400 (BAD REQUEST) with message  "Value of <parameter-name-values> exceeded max value of <the-max-value>".

**Invalid parameter value(s)**
- If <parameter-name> does not contain one of the following acceptable parameter values: <comma-delimeted-list-of-valid-parameters> return HTTPS status 400 with message "Invalid <parameter-name> value provided"

  
## Testing

Document the endpoints with a brief description on top of the src/mi_api/routers/<api-name>.py file.

Create test harness in the tests/api folder

Update the following  file /docs/mi_api/testing-documentation.md with instructions on how to run the test harness for the <api-name> API. 

Add the new api to the docs url http://localhost:8000/docs.



