# Add method <method-name> to <domain-name> FMP Provider

## Preamble

Before moving forward stop here and read the **pre-execution review** document located in this file: 
```code
.github/prompts/prompt_templates/pre-execution-reviews/pre-execution-basic-review.md 
```
and then we can proceed with the prompt below as directed. 

### Adapter Class to be created
- **Create Class** FMP<domain-name>Adapter in **file** fmp_<domain-name>.py 

### Adapter Class Methods to be created
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

**Context:**
- Architecture: 		docs/sdk-architecture.md
- SDK Design: 		  docs/sdk-architecture.md
- FMP Provider Directory: src/mi_sdk/providers/fmp
- Exception         Handling:	docs/exception-handling.md

**Constraints:**
- Must follow .github/copilot-instructions.md
- Must not expose provider-specific logic in the SDK service

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