# Build Get Company FMP Provider

## Preamble

Before moving forward stop here and read the **pre-execution review** document located in this file: 
```code
.github/prompts/prompt_templates/pre-execution-basic-review.md 
```
and then we can proceed with the prompt below as directed. 

### Adapter Class to be created
- **Create Class** FMPCompanyAdapter in **file** fmp_company.py 

### Adapter Class Methods to be created
- **Method:** get_profile() 
  - **Description** - calls FMP API to get the company profile 
  - **Inputs**: A stock symbol.
  - **Response**: returns the FMP API JSON structure as-is for the given symbol
  - **Method Comment:** In the method add following comment
    - This service return a full company profile
  
### FMP API Endpoint
- **Sample Endpoint:** GET https://financialmodelingprep.com/stable/profile?symbol=AAPL&apikey=YOUR_API_KEY

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

### Validation
After creating the required methods in the FMPCompany Adapter, create separate file called fmp_company_run.py. Create code in such a way that when I run it from the command line with no parameters it should prompt me for what FMP service I would like to run (while displaying a list of  available services(aka methods)). When I enter the method name, it should prompt me for parameters while also displaying an example of the parameters I need to enter next. After entering the parameters, it executes and writes response or exceptions to standard output. 

### Comments
Add a comment on the top of the fmp_company_run.py file that provides the exact syntax for running the fmp_company_run.py validation code from Windows Powershell and syntax for also running it form gitbash command line.