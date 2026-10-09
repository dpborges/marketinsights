# Add method to the MarketInsights Provider

## Preamble

Before moving forward stop here and read the **pre-execution review** document located in this file: 
```code
.github/prompts/prompt_templates/pre-execution-reviews/pre-execution-basic-review.md 
```
and then we can proceed with the prompt below as directed. 

### Role and Objective

You are an expert Python developer who is experienced in the MarketInsights market data services stack.  

The objective of this prompt is to expose an FMP provider service via an Adapter which allows us to decouple Provider implementation from SDK implementation (layer above). 

**Context:**
- Architecture: 		  .gitlab/copilot-instructions.md
- FMP Provider Directory: src/mi_sdk/providers/fmp
- Exception           Handling:	prompts/exception_management/exception_management.md
  
**Constraints:**
- Must follow .github/copilot-instructions.md

### Adapter Class Method(s) to be updated
- **Method Name:** <provider-method-name1>() 
  - **Description** - <provider-method-description1>
  - **Inputs**: <provider-input-names1>.
  - **Response**: returns the FMP API JSON structure while also conforming to the exception handling pattern for the Provider layer. This  is covered in the "Exceptions" section.
  - If provider-optional-method-comment1-flag is set to yes include the Method Comment(Optional) below
  - **Method Comment(Optional):** Above the method, add following comment:
    - <provider-optional-method-comment1>
  - other wise ignore.

### FMP API Endpoint

- **FMP Provider endpoint to use:**  <provider-method-name1-endpoint>

### API Key

- Use API KEY found in the .env file. The property name is MARKET_FMP_API_KEY

### General Implementation instructions

Here is the file in we would like to add method to.

- FMP Adapter:    fmp_<domain-name>.py

### Provider Implementation instructions

Return Provider JSON response as-is while adhering to Exceptions section of this document.

### Exceptions 

Follow instructions in this document 
```code .github/prompts/exception_management/exception_management.md.```
for implementing the relevant Exception handling pattern for the Provider layer. 

## Business Logic

No specific business logic is being implemented

### FMP Provider Validation run file 

After creating the required methods in the FMP<domain-name> Adapter, create separate file called fmp_<domain-name>_run.py. 

On top of the fmp_<domain-name>_run.py file, define the METHODS variable that contains a dictionary with the available methods and their associated descriptions.

For example,

```python
METHODS = {
    "method name 1 here": "method 1 description here",
    "method name 2 here": "method 2 description here",
    ...
}
``` 
Include the methods found in the section of this prompt called
"Adapter Class Methods to be created".

In the fmp_<domain-name>_run.py file create code in such a way that when I run it from the command line with no parameters it should prompt me with a list of methods from the METHODS dictionary. When I enter a method name, it should prompt me for parameters for that method name while also displaying an example of the parameters I need to enter. After entering the parameters, it executes and writes response or exceptions to standard output. 

### FMP Provider Comments

Add a comment on the top of the fmp_<domain-name>_run.py file that provides the exact syntax for running the fmp_<domain-name>_run.py validation code from either the Windows Powershell or syntax for also running it from gitbash command line.

