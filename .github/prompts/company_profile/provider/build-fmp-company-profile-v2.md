# Build Get Company FMP Provider


## Role and Objective

You are a Python developer and are very good at maintaining code and testing it to validate the changes before acknowledging that the change is completed.

We would like to you to update the FMP Company Provider so that it employs the Exception handling pattern for Providers, that is documented in file 
```code .github/prompts/exception_management/exception_management.md.```
If an error is encountered, it should display the attributes in the error property in the payload. If request is successful,  the error property should show in the response  payload as empty  { "error": {} }.

### Adapter Class to be updated
- **Modify Class** FMPCompanyAdapter in **file** fmp_company.py 

### Adapter Class Methods to be updated
- **Method:** get_profile() 
  - **Description** - calls FMP API to get the company profile 
  - **Inputs**: A stock symbol.
  - **Response**: returns the FMP API JSON structure as-is for the given symbol
  
  
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
After updating the required methods in the FMPCompany Adapter, update the file called fmp_company_run.py, only if needed. Run it yourself to ensure exceptions are showing in the payload as described in the Objective in this prompt and how it is documented in file 
```code .github/prompts/exception_management/exception_management.md.```

### Comments
Update comment on the top of the fmp_company_run.py file that provides, if any changes to syntax for runnning from command line.