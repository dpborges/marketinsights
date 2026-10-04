# Add method <method-name> to <domain-name> FMP Provider

## Preamble

Before moving forward stop here and read the **pre-execution review** document located in this file: 
```code
.github/prompts/_prompt_templates/pre-execution-reviews/pre-execution-basic-review.md 
```
and then we can proceed with the prompt below as directed. 

### Role and Objective

You are a Python developer who is experienced in buidling the three layers of the MarketInsights market data services stack.

The objective of this prompt is to expose an FMP service via the Market Insights API. It can be considered as pass-through, although we still want to maintain all of the three layers of the architecture stack:

- API  (REST API layer)
- SDK  (Business Layer) 
- FMP Provider  (Provider layer)

The objective of this prompt is to 
- 1) add a new method to an existing FMP Adapter that exposes an FMP API endpoint
- 2) add the method to the corresponding SDK 
- 3) add it to the existing <api-name> router file.

As you add the method to each of the layers, adhere to the Exception management pattern for each of the respective layers.

Here are the files in scope of this new capibility.

- FMP Adapter:    fmp_<domain-name>.py
- SDK file:       <sdk-service-name>_service.py
- FASTAPI file:   <api-name>.py   

**Context:**
- Architecture: 		  .gitlab/copilot-instructions.md
- SDK Design: 		    docs/sdk-architecture.md
- FMP Provider Directory: src/mi_sdk/providers/fmp
- SDK Directory       src/mi_sdk/services
- FASTAPI Directory:  src/mi_api
- Exception           Handling:	docs/exception-handling.md

**Constraints:**
- Must follow .github/copilot-instructions.md
- Must not expose provider-specific logic in the SDK service

### Adapter Class to be updated
- **Class Name** FMP<domain-name>Adapter in **file** fmp_<domain-name>.py 

### Adapter Class Method(s) to be created
- **Method Name:** <method-name>() 
  - **Description** - <provide-method-description>
  - **Inputs**: <comma-delimeted-list-of-input-names>.
  - **Response**: returns the FMP API JSON structure as-is for the given inputs
  - **Method Comment(Optional):** Above the method, add following comment:
    - <enter-optional-method-comment-here>


### SDK Class Method(s) to be created
- **Method Name:** <method-name>() 
  - **Description** - <provide-method-description>
  - **Inputs**: <comma-delimeted-list-of-input-names>.
  - **Response**: returns the FMP API JSON structure as-is for the given inputs
  - **Method Comment(Optional):** Above the method, add following comment:
    - <enter-optional-method-comment-here>


### FMP API Endpoint
- **Sample Endpoint:** GET <fully-qualified-url>

### API Key
- Use API KEY found in the .env file. The property name is MARKET_FMP_API_KEY


### Implementation instructions
This section intentionally left blank

### Validation run file
After creating the required methods in the FMP<domain-name> Adapter, create separate file called fmp_<domain-name>_run.py. 

On top of the fmp_<domain-name>_run.py file, define the METHODS variable value with a dictionary of the available methods and their associated descriptions found in the section of this prompt called
"Adapter Class Methods to be created".

For example

```python
METHODS = {
    "method name 1 here": "method 1 description here",
    "method name 2 here": "method 2 description here",
    ...
}
``` 

In the fmp_<domain-name>_run.py file create code in such a way that when I run it from the command line with no parameters it should prompt me with a list of methods from the METHODS dictionary. When I enter a method name, it should prompt me for parameters for that method name while also displaying an example of the parameters I need to enter. After entering the parameters, it executes and writes response or exceptions to standard output. 

### Comments
Add a comment on the top of the fmp_company_run.py file that provides the exact syntax for running the fmp_<domain-name>_run.py validation code from either the Windows Powershell or syntax for also running it from gitbash command line.