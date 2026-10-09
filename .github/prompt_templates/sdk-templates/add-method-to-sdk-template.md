# Add method to SDK

## Preamble

Before moving forward stop here and read the **pre-execution review** document located in this file: 
```code
.github/prompts/prompt_templates/pre-execution-reviews/pre-execution-basic-review.md 
```
and then we can proceed with the prompt below as directed. 

## Role and Objective

You are a Python SDK developer that has been asked to add a method to an SDK service that utilizes the fmp-<domain-name>.py provider.
- You will addding the method to the SDK file called <sdk-service-name>_service.py 

**Context:**
- Architecture: 		  .gitlab/copilot-instructions.md
- SDK Design: 		    docs/sdk/architecture.md
- SDK Directory       src/mi_sdk/services
- SDK Test Directory  .github/test/sdk
- FMP Provider Directory: src/mi_sdk/providers/fmp
- Exception Handling:	.gitlab/prompts/exception_management/exception_management.md

**Constraints:**
- Must follow .github/copilot-instructions.md
- Must not expose provider-specific logic in the SDK service

### SDK Class Method(s) to be added
- **Method Name:** <sdk-method-name1>() 
  - **Description** - <sdk-method-description1>
  - **Inputs**: <sdk-input-names1>.
  - **Response**: returns the FMP API JSON structure while also conforming to the exception handling pattern for the SDK layer. That is covered in the "Exceptions" section of this prompt.
  - If sdk-optional-method-comment1-flag is set to yes include the Method Comment(Optional) below
   - **Method Comment(Optional):** Above the method, add following comment:
    - <sdk-optional-method-comment1>
  - other wise ignore.


## Response:

**Sample JSON response for <sdk-method-name1>**

```json
{
  "companies": [
  {
    "symbol": "NVDA",
    "currentPrice": 200.00,
    "horizons": {
      "SHORT": {
        "stopLoss": {
          "price": 185.00,
          "downsidePct": 7.50,
          "method": "SUPPORT_ATR"
        },
        "support": {
          "price": 188.00,
          "strength": 0.84,
          "touches": 3
        },
        "volatility": {
          "atr": 6.00,
          "atrPeriod": 14,
          "atrTimeframe": "DAILY",
          "bufferMultiplier": 0.50
        }
      }
    }
  }
]
```

### SDK Implementation instructions

**Multi-symbol support per request**

Check statement below, to see if SDK should support multi-symbol request.

- Endpoint support multi-symbol request:  <sdkSupportsMultiSymbolRequests>

If yes, then the SDK should implement a python AsyncPipeLine to be able to submit up-to 10 symbols per request.

If no, the SDK does not need to implement AsyncPipeLine as it will accept one symbol per request.

**Precision for Floating Point Numbers**

Any floating numbers properties that are returned in the SDK JSON response that are floating point numbers with more than 6 decimal places should be rounded to 2 decimal places by default. 

If the statement below 

  Has properties with precision greater than 2 = <PropsWithPrecisionGT2>

is equal to yes, use the precisions provided for the properties listed in the Prompt config parameter "higherPrecisionProperties".  This will have the property names and the desired precision.

If statement is equal to "no", 
default to a precision of 2 for floating point numbers being returned by SDK.

### Exceptions 

Follow instructions in this document 
```code .github/prompts/exception_management/exception_management.md.```
for implementing the relevant Exception handling pattern for each of the layers. 

## Business Logic

No specific business logic is being implemented

## SDK Validation Logic

The SDK <method-name>() will accept <number> parameters
- <parameter-name>: <parameter-description>; Sample values are: <sample-value(s)>
  
**Parameter Missing Errors**
- If the mandatory <parameter-name> parameter is omitted, return message "Parameter <parameter-name> missing" and follow the default policy for SDK behavior in the Exception management file located in the 'Exceptions' section of this prompt.

**Parameter Values Missing errors**
- If the <parameter-name> is provided with no values, return message  "No <parameter-name-values> provided"  and follow the default policy for SDK behavior in the Exception management file located in the 'Exceptions' section of this prompt.

Ignore empty entries, so it works, for example symbols=,META,APPL works.

**Defaults**
- If <parameter-name> parameter is omitted, default it to <parameter-name>=<default-value>

**Maximum value exceeded**
- If the value of <parameter-name> exceeds the max value of <the-max-value> return "Value of <parameter-name-values> exceeded max value of <the-max-value>" and follow the default policy for SDK behavior in the Exception management file located in the 'Exceptions' section of this prompt.

**Invalid parameter value(s)**
- If <parameter-name> does not contain one of the following acceptable parameter values: <comma-delimeted-list-of-valid-parameters> return HTTPS status 400 with message "Invalid <parameter-name> value provided" and follow the default policy for SDK behavior in the Exception management file located in the 'Exceptions' section of this prompt.

## SDK Testing

- Create a separate test file “test_<sdk-service-name>_service.py” in the SDK Test directory. 
- Include <number> tests. 
  - One to handle <sdk-test-method1> with following parameters: <sdk-test-param1>=<sdk-test-value1>
  - One to handle <sdk-test-method2> with following parameters: <sdk-test-param2>=<sdk-test-value2>
  - ....
- Add a docstring at the top of the file with the syntax for running the test from gitbash terminal.

## SDK Documentation

Update the following file /docs/mi_api/testing-documentation.md with instructions on how to run the test harness for the <sdk-service-name> API. 

If the <sdk-service-name> service has fairly complex business logic and validation logic, create a document in the docs/sdk/<sdk-service-name>-service.md file to explain the overarching goal and salient points so the reader would understand it, if they happen to make modifications and adjustments to the business logic and/or implementation in the future.


