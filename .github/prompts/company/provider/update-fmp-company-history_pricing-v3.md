# Update Company FMP Provider to render company history pricing

## Preamble

Before moving forward stop here and read the **pre-execution review** document located in this file: 
```code
.github/prompts/_prompt_templates/pre-execution-basic-review.md 
```
and then we can proceed with the prompt below as directed. 

### Adapter Class to be updated
- **Update the Class** FMPCompanyAdapter in **file** fmp_company.py 

### Adapter Class Method to be created
- **Method:** get_historical_pricing() 
- **Description** - calls FMP API to get a company's historical pricing 
- **Inputs**: A stock symbol, from_date, to_date 
- **Response**: returns the FMP API JSON structure as-is for the given symbol
  
  
### FMP API Endpoint
- **Sample Endpoint:** GET https://financialmodelingprep.com/stable/historical-price-eod/full?symbol=NVDA&from=2026-03-01&to=2026-09-28&apikey=YOUR_API_KEY

### API Key
- Use API KEY found in the .env file. The property name is MARKET_FMP_API_KEY

**Context:**
- Architecture:     .github/copilot-instructions.md
- SDK Design:       .github/copilot-instructions.md
- FMP Provider Directory: src/mi_sdk/providers/fmp
- Exception Handling:	.github/prompts/exception_management/

**Constraints:**
- Must follow .github/copilot-instructions.md
- Must not expose provider-specific logic in the SDK service

### Validation
- Required paramaters: Symbol, from_date and to_date. 
- Expected from_date and to_date format is YYYY-MM-DD.
- validate real calendar dates and require from_date <= to_date.
- If no dates are provided, raise error based on the exceptions management guidance.



### Manual Testing Script
After creating the required method, get_historical_pricing(),  in the FMPCompany Adapter, update the file called fmp_company_run.py in such a way that when I run it from the command line with no parameters it should prompt me for what FMP service I would like to run (while displaying a list of  available services(aka methods)). When I enter the method name, it should prompt me for parameters while also displaying an example of the parameters I need to enter next. After entering the parameters, it executes and writes response or exceptions to standard output. 

### Exceptions
After updating the file called fmp_company_run.py, run it yourself to ensure the exception pattern  is showing in the payload as described here 
```code .github/prompts/exception_management/exception_management.md.``` 

### Comments
Add a comment on the top of the fmp_company_run.py file that provides the exact syntax for running the fmp_company_run.py validation code from Windows Powershell and syntax for also running it form gitbash command line.