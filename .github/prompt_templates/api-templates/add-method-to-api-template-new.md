# Add method to FASTAPI 

**Context:**
- Architecture: 		  .gitlab/copilot-instructions.md
- SDK Design: 		    docs/sdk/architecture.md
- SDK Directory       src/mi_sdk/services
- FASTAPI Directory:  src/mi_api
- FASTAPI Router:     <domain-name>
- Exception           Handling:	docs/exception-handling.md

**Constraints:**
- Must follow .github/copilot-instructions.md

### FAST API Router method to be updated
- **Method Name:** <fastapi-method-name1>() 
  - **Description** - <fastapi-method-description1>
  - **Inputs**: <fastapi-input-names1>.
  - **Response**: returns the SDK JSON structure while also conforming to the exception handling pattern for the FASTAPI layer, that is covered in the "Exceptions" section.


### FASTAPI Implementation instructions

The REST API should support making requests for up to 10 symbols.
For example,  symbols=AAPL,SPCX,TER,NVDA ... LAST

The <domain-name> API should expose the following SDK method(s):
  - <sdk-method-name1>
  
The API will accept <number> parameters
- <parameter-name1>: <sample-value(s)>
- <parameter-name2>: <sample-value(s)>

The SDK service to be used for this API is called: <sdk-service-filename>
and can be found in the SDK directory:   src/mi_sdk/services

### SAMPLE URL GET Requests

- Endpoint1: /api/v1/<domain-name>/<sub-domain-name>?symbols=META&horizons=SHORT,MEDIUM
- Endpoint2: /api/v1/<domain-name>/<sub-domain-name>?symbols=IBM&horizons=short,medium

When endpoint /api/v1/<domain-name>/<sub-domain-name> is called,
it invokes the <sdk-method-name1> method on the file <sdk-service-filename> SDK.

The API returns the JSON object from the respective <sdk-method-name1> method "as-is".
The API should understand how to map exceptions from the SDK to the HTTP response using guidance in the Exceptions section of this prompt.


### Exceptions 

Follow instructions in this document 
```code .github/prompts/exception_management/exception_management.md.```
for implementing the relevant Exception handling pattern for the API layer. 

## Business Logic
section intentionlly left empty as business logic should be in the SDK layer.

### FASTAPI Validations and Defaults

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


## FASTAPI Testing

Document the endpoints with a brief description on top of the src/mi_api/routers/<domain-name>.py file.

Create test harness in the folder tests/api

## API Documentation

Update the following file /docs/mi_api/testing-documentation.md with instructions on how to run the test harness for the <domain-name> API. 

Add the new api to the docs url http://localhost:8000/docs.
