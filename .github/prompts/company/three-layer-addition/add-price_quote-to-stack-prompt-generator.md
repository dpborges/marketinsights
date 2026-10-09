# Add method to the MarketInsights Stack

## Prompt Generation Instructions.
You are a prompt generator. You will not be executing this prompt except for the instructions provided here in this section.
You are only going to generate a new prompt markdown file from this prompt.
Read the "Prompt Config Parameters" below and substitute the values
with the corresponding parameter names, in angle brackets < >, and generate a new file called: add-price-quote-prompt.md 
in this folder  .github/prompts/company/three-layer-addition

In the new file, exclude this section and exclude the "Prompt Config Parameters" section.

The new generated markdown file should start with the Preamble section and include everything after that. All the config parameters in angle brackets should have been replaced with their values from the Prompt Config Parameters section.

If you cannot find a value in Prompt Config parameters to replace a value in angle brackets, within the prompt, leave the angle brackets with the enclosing text as is.

When you are done generating the file, you can stop.

## Prompt Config Parameters
domain-name: Company
api-name: Company
sdk-service-name: CompanyService

provider-method-name1: get_current_price_quote
provider-method-name1-description1: return realtime price quote for given stock
provider-method-name1-number-of-params: 1
provider-method-name1-params: symbol
provider-method-name1-optional-comment-flag: no
provider-method-name1-optional-comment: "no comment"
provider-method-name1-endpoint:  https://financialmodelingprep.com/stable/quote-short?symbol=NVDA&apikey=
PropsWithPrecisionGT2: no
higherPrecisionProperties: [ 
                            { "property-name1": "precision1": 2, }, 
                            { "property-name2": "precision2": 2 } 
                         ]


sdk-method-name1: get_current_price_quote
sdk-method-name1-description: return realtime price quote for 1 or up to 10 stock symbols
sdk-method-name1-number-of-params: 1
sdk-method-name1-params: symbols
sdk-method-name1-optional-comment-flag: no
sdk-method-name1-optional-comment: "no comment"
sdkSupportsMultiSymbolRequests: yes
sdk-test-method-name1: get_current_price_quote
sdk-test-method-name1-param: symbols
sdk-test-method-name1-value: NVDA,GLW,STM,CAT,VST


fastapi-method-name1: get_current_price_quote
fastapi-method-name1-description: "Returns the realtime price for one or more stock symbols" 
fastapi-method-name1-params: symbols
fastapi-method-name1-optional-comment-flag: no
fastapi-method-name1-optional-comment: "none"


## Preamble

Before moving forward stop here and read the **pre-execution review** document located in this file: 
```code
.github/prompts/prompt_templates/pre-execution-reviews/pre-execution-basic-review.md 
```
and then we can proceed with the prompt below as directed. 

### Role and Objective

You are a Python developer who is experienced in building the three layers of the MarketInsights market data services stack. For more information on the stack you can look at the content referenced in the "Context"  section of this prompt. You can also look an example implementation such as the Company provider, Sdk, and FASTAPI.

The objective of this prompt is to expose an FMP service via the Market Insights API. Even if there is no business logic and may seem like a pass-through, we still want to maintain all of the three layers of the architecture stack:

- API  (REST API layer)
- SDK  (Business Layer) 
- FMP Provider  (Provider layer)

We don't want the FASTAPI calling the FMP Provider directly.

The objective of this prompt is to 
- 1) add a new method to the existing FMP<domain-name> Adapter that exposes an FMP API endpoint
- 2) add a method to the corresponding SDK <sdk-service-name> that calls the new FMP Adapter method name
- 3) add a method to the existing <api-name> router file that calls the new SDK Service method.

The implementation should be done in a stepwise fashion, one layer at a time.

Step (1) First implement the FMP Provider and test it. Complete documenation instructions for this layer. After successful testing move to step 2. 

Step (2) Implement the SDK and test it. Complete documentation instructions for this layer. After successful testing move to step 3. 

Step (3) Implement the FAST API layer and test it. Complete documenation instructions for this layer as well.


**Context:**
- Architecture: 		  .gitlab/copilot-instructions.md
- SDK Design: 		    docs/sdk-architecture.md
- FMP Provider Directory: src/mi_sdk/providers/fmp
- SDK Directory       src/mi_sdk/services
- FASTAPI Directory:  src/mi_api
- FASTAPI Router:     <domain-name>
- Exception           Handling:	docs/exception-handling.md

**Constraints:**
- Must follow .github/copilot-instructions.md
- Must not expose provider-specific logic in the SDK service

### Adapter Class Method(s) to be created
- **Method Name:** <provider-method-name1>() 
  - **Description** - <provider-method-name1-description>
  - **Inputs**: <provider-method-name1-params>.
  - **Response**: returns the FMP API JSON structure while also conforming to the exception handling pattern for the Provider layer, that is covered in the "Exceptions" section.
  - If provider-method-name1-optional-comment-flag is set to yes,  include the Method Comment(Optional) below
  - **Method Comment(Optional):** Above the method, add following comment:
    - <provider-method-name1-optional-comment>
  - other wise ignore.

### SDK Class Method(s) to be created
- **Method Name:** <sdk-method-name1>() 
  - **Description** - <sdk-method-name1-description>
  - **Inputs**: <sdk-method-name1-params>.
  - **Response**: returns the FMP API JSON structure while also conforming to the exception handling pattern for the SDK layer, that is covered in the "Exceptions" section.
  - If sdk-optional-method-comment1-flag is set to yes include the Method Comment(Optional) below
   - **Method Comment(Optional):** Above the method, add following comment:
    - <sdk-method-name1-optional-comment>
  - other wise ignore.

### FAST API Router method be created
- **Method Name:** <fastapi-method-name1>() 
  - **Description** - <fastapi-method-name1-description>
  - **Inputs**: <fastapi-method-name1-params:>.
  - **Response**: returns the FMP API JSON structure while also conforming to the exception handling pattern for the REST API layer, that is covered in the "Exceptions" section.
  - **Method Comment(Optional):** Above the method, add following comment:
    - <fastapi-method-name1-optional-comment>

### FMP API Endpoint

- **FMP Provider endpoint to use:**  <provider-method-name1-endpoint>

### API Key

- Use API KEY found in the .env file. The property name is MARKET_FMP_API_KEY

### General Implementation instructions

Here are the files in scope of this new capability.

- FMP Adapter:    fmp_<domain-name>.py
- SDK file:       <sdk-service-name>_service.py
- FASTAPI file:   <api-name>.py   

As you add the method to each of the three layers, adhere to the Exception management pattern for each of the respective layers.

### Provider Implementation instructions
This section intentionally left blank

### SDK Implementation instructions

**Multi-symbol support per request**

Check statement below, to see if SDK should support multi-symbol request.

- Endpoint support multi-symbol request: <sdkSupportsMultiSymbolRequests>

If yes, then the SDK should implement a python AsyncPipeLine to be able to submit up-to 10 symbols per request.

If no, the SDK does not need to implement AsyncPipeLine as it will accept one symbol per request.

**Precision for Floating Point Numbers**

Any floating numbers properties that are returned in the SDK JSON response that are floating point numbers with more than 6 decimal places should be rounded to 2 decimal places by default. 

If the statement below 

  Has properties with precision greater than 2 = <PropsWithPrecisionGT2>

is equal to yes, use the precisions provided for the properties listed in the Prompt config parameter "higherPrecisionProperties".  This will have the property names and the desired precision.

If statement is equal to "no", 
default to a precision of 2 for floating point numbers being returned by SDK.

### FASTAPI Implementation instructions

The REST API should support making requests for up to 10 symbols.
For example,  symbols=AAPL,SPCX,TER,NVDA ... LAST


### Exceptions 

Follow instructions in this document 
```code .github/prompts/exception_management/exception_management.md.```
for implementing the relevant Exception handling pattern for each of the layers. 

## Business Logic
section intentionlly left empty

## SDK Validation Logic

The SDK <sdk-method-name1>() will accept <sdk-method-name1-number-of-params> parameters
- <sdk-method-name1-params>: <sdk-parameter-description>; Sample values are: <sample-value(s)>
  
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

### API Validations and Defaults

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

### FMP Provider Validation run file 

After creating the required methods in the FMP<domain-name> Adapter, create separate file called fmp_<domain-name>_run.py. 

On top of the fmp_<domain-name>_run.py file, define the METHODS variable value with a dictionary of the available methods and their associated descriptions. 

For example,

```python
METHODS = {
    "method name 1 here": "method 1 description here",
    "method name 2 here": "method 2 description here",
    ...
}
``` 
Include the methods found in the section of this prompt called
"Adapter Class Methods to be created"

In the fmp_<domain-name>_run.py file create code in such a way that when I run it from the command line with no parameters it should prompt me with a list of methods from the METHODS dictionary. When I enter a method name, it should prompt me for parameters for that method name while also displaying an example of the parameters I need to enter. After entering the parameters, it executes and writes response or exceptions to standard output. 

### FMP Provider Comments

Add a comment on the top of the fmp_<domain-name>_run.py file that provides the exact syntax for running the fmp_<domain-name>_run.py validation code from either the Windows Powershell or syntax for also running it from gitbash command line.

## SDK Testing

- Create a separate test file “test_<sdk-service-name>_service.py” in the SDK Test directory. 
- Include <number> tests. 
  - One to handle <sdk-test-method1> with following parameters: <sdk-test-param1>=<sdk-test-value1>
  - One to handle <sdk-test-method2> with following parameters: <sdk-test-param2>=<sdk-test-value2>
  - ....
- Add a docstring on top of the file with the syntax for running the test from gitbash terminal.

## SDK Documentation

Update the following  file /docs/mi_api/testing-documentation.md with instructions on how to run the test harness for the <sdk-service-name> API. 

If the <sdk-service-name> service is complicated and has extensive business logic and validation rules, create a document in the docs/sdk/<sdk-service-name>-service.md file capturing overarching goal and salient points the reader should understand if they plan to make modifications and adjustments to the business logic and/or implementation in the future.

## API Testing

Document the endpoints with a brief description on top of the src/mi_api/routers/<api-name>.py file.

Create test harness in the tests/api folder

## API Documentation

Update the following file /docs/mi_api/testing-documentation.md with instructions on how to run the test harness for the <api-name> API. 

Add the new api to the docs url http://localhost:8000/docs.
