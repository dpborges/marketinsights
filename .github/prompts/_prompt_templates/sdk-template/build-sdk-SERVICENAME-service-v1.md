Build <sdk-service-name> SDK service

## Preamble

Before moving forward stop here and read the **pre-execution review** document located in this file: 
```code
.github/prompts/_prompt_templates/pre-execution-reviews/pre-execution-basic-review.md 
```
and then we can proceed with the prompt below as directed. 

## Role and Objective

You are a Python SDK developer that has been asked to create an SDK service that utilizes the fmp-<domain-name>.py provider.
- Create a <sdk-service-name> service SDK in a separate file called <sdk-service-name>_service.py 

### SDK Class to be created
- **Create Class** <sdk-service-name>Service in **file** <sdk-service-name>_service.py file

### SDK Class Method(s) to be created
- **Method Name:** <method-name1>() 
  - **Description** - <provide-method-description1>
  - **Inputs**: <comma-delimeted-list-of-input-names1>.
  - **Response**: returns the FMP API JSON structure as-is for the given inputs
  - **Method Comment(Optional):** Above the method, add following comment:
    - <enter-optional-method-comment-here>
  
**Context:**
- Architecture:       	  .github/copilot-instructions.md
- SDK Design:        	    .github/copilot-instructions.md
- SDK Architecture:       docs/sdk/architecture.md
- Exception Handling:	    .github/prompts/exception_management/exception_management.md
- SDK Services Directory  src/mi_sdk/services
- SDK Test Directory      tests/sdk
- FMP providers Directory src/mi_sdk/providers/fmp
- FMP <domain-name> provider    fmp_<domain-name>.py 

## Constraints:
- Must follow .github/copilot-instructions.md
- Must not expose provider-specific logic in the SDK service

**Sample JSON response for <method-name1>()**
```json
{
  "propert1": [
    { 
      "symbol": "NVDA", 
      "name": "Nvidia",
    }, 
      { 
      "symbol": "IBM", 
      "name": "Internation Business Machines",
    }, ,
  ],
   "errors": [
    ...
  ],
  "summary": {
    "requested": 1,
    "successful": 1,
    "failed": 0
  }
}
```

**Sample JSON response for <method-name2>()**
```json
{
  "propert1": [
    { 
      "symbol": "NVDA", 
      "name": "Nvidia",
    }, 
      { 
      "symbol": "IBM", 
      "name": "Internation Business Machines",
    }, ,
  ],
   "errors": [
    ...
  ],
  "summary": {
    "requested": 1,
    "successful": 1,
    "failed": 0
  }
}
```

## Implementation Details**
Any floating numbers properties that are returned in the SDK JSON response that are floating point numbers with more than 10 decimal places should be rounded to 2 decimal places. If there is property I need slightly more precision, for example for normalizing scores, they will provide here. 
  
    <property-name>: <precision>
    score: round to 3 decimal places
If there is no properties provided, default to 2 decimal places.




## use AsyncPipeline for <calling-method-name>() method
Since the <method-name>() method in the fmp_<domain-name>.py provider only supports a single  parameter, I would like this SDK to implement an AsyncPipeLine to be able to handle running  
several instances of the <method-name1>() with different parameters using Python AsyncPipeline. An example usage is documented here: .gitlub/prompts/_prompt_templates/implementation-templates.

The idea is for the SDK to have the ability to accept a parameter list (not just one) and call the respective fmp_<domain-name> adapter method for each parameter in parallel. Wait until all method calls are completed for each parameter, and get the overall response for each parameter, and return all responses at once. 

The SDK <coordinator-method-name>() will set up the AsyncPipeline and function as the caller and coordinator.
The <coordinator-method-name>() will use Option#<number> below for this implementation:

**Option#1**
The <coordinator-method-name>()  will call 
- <calling-method-name>
for each paramater in the parameter list in parallel.

**Option#2**
The <coordinator-method-name>()  will call the following methods in parallel
- <calling-method-name1>
- <calling-method-name2>
- <calling-method-name3>
with the same parameter in parallel.

# Usage
section intentionlly left empty

## Business Logic
section intentionlly left empty

## Validation Logic

The SDK <method-name1>() will accept <number> parameters
- <parameter-name>: <parameter-description>; Sample values are: <sample-value(s)>
  
**Parameter Missing Errors**
- If the mandatory <parameter-name> parameter is omitted, return message "Parameter <parameter-name> missing" and follow the default policy for SDK behavior in the Exception management file located in the 'Exceptions' section of this prompt.

**Parameter Values Missing errors**
- If the <parameter-name> is provided with no values at, return message  "No <parameter-name-values> provided"  and follow the default policy for SDK behavior in the Exception management file located in the 'Exceptions' section of this prompt.

Ignore empty entries, so it works, for example symbols=,META,APPL works.

**Defaults**
- If <parameter-name> parameter is omitted, default it to <parameter-name>=<default-value>

**Maximum value exceeded**
- If the value of <parameter-name> exceeds the max value of <the-max-value> return "Value of <parameter-name-values> exceeded max value of <the-max-value>" and follow the default policy for SDK behavior in the Exception management file located in the 'Exceptions' section of this prompt.

**Invalid parameter value(s)**
- If <parameter-name> does not contain one of the following acceptable parameter values: <comma-delimeted-list-of-valid-parameters> return HTTPS status 400 with message "Invalid <parameter-name> value provided" and follow the default policy for SDK behavior in the Exception management file located in the 'Exceptions' section of this prompt.

## Exceptions
Have the <sdk-service-name> SDK employ the Exception handling pattern for SDK services, that is documented in file 
```code .github/prompts/exception_management/exception_management.md.```

## Testing

- Create a separate test file “test_<sdk-service-name>_service.py” in the SDK Test directory. 
- Include <number> tests. 
  - One to handle <method-name> with following parameters: <param-name>=<param-value>
  - One to handle <method-name> with following parameters: <param-name>=<param-value>
  - ....
- Add a docstring on top of the file with the syntax for running the test from gitbash terminal.


## Documentation

Update the following  file /docs/mi_api/testing-documentation.md with instructions on how to run the test harness for the <sdk-service-name> API. 

Add the new api to the docs url http://localhost:8000/docs.

If the <sdk-service-name> service is complicated and has extensive business logic and validation rules, create a document in the docs/sdk/<sdk-service-name>-service file capturing overarching goal and salient points the reader should understand if they plan to make modifications and adjustments to the business logic and/or implementation in the future.








