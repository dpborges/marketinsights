Build RiskRewardProfile SDK service

## Preamble

Before moving forward stop here and read the **pre-execution review** document located in this file: 
```code
.github/prompts/prompt_templates/pre-execution-basic-review.md 
```
and then we can proceed with the prompt below as directed. 

## Role and Objective

You are a Python SDK developer that has been asked to create a service that returns a company profile using the fmp-company.py provider.
- Create a company service SDK in a separate file called company_service.py. 

### SDK Class to be created
- **Create Class** CompanyService in **file** company.py file

### SDK Class Methods to be created
- **Method:** get_profile() 
  - **Description** - calls the get_profile method in the SDK fmp_company.py file
  - **Inputs**: A stock symbol or list of stock symbols, upto 10 symbols maximum.
  - **Response**: it will return the JSON from the get_profile method, as-is. 
  
- **Method:** get_current_summary() 
  - **Description** calls the get_profile method in the SDK fmp_company.py file and returns a subset of the fields listed in the output of the get_profile() method response. 
  - **Inputs**: A stock symbol or list of stock symbols, upto 10 symbols maximum.
  - **Response**: the method will modify response from get_profile to return the following response JSON structure. 
  
**Context:**
- Architecture:       	docs/sdk-architecture.md
- SDK Design:        	  docs/sdk-architecture.md
- Exception Handling:	docs/exception-handling.md
- SDK Services Directory  src/mi_sdk/services
- FMP providers Directory  src/mi_sdk/providers/fmp
- FMP company provider  fmp_company.py 

**Constraints:**
- Must follow .github/copilot-instructions.md
- Must not expose provider-specific logic in the SDK service


REVIEW FROM THIS POINT FORWARD FOR ACCURACY


**Sample JSON response for get_summary()**
```json
{
  "companies": [
    { 
      "symbol": "NVDA", 
      "name": "Nvidia",
      "price": 270,
      "sector": "Technology",
      "industry": "Consumer Electronics",
    }, 
    {
      "symbol": "IBM", 
      "name": "Internationl Business Machines",
      "price": 181,
      "sector": "Technology",
      "industry": "Consumer Electronics",
    },
    “errors”: [
        <capture errors/exceptions here>
    ]
  ]
}
```

## Implementation Details**
Since the get_profile method in the fmp_company.py provider only supports a single symbol parameter, in this SDK implement the ability to accept multiple symbols and call the respective fmp_company adapter method for each symbol in parallel. Wait until all method calls are completed for each symbol, get the overall recommendation for each symbol, map the companyName to  name in the get_summary() JSON result and return response all at once using the JSON response provided in the Sample JSON response section above. If a call failed for one or two symbols , return the others and capture the error for the given symbols in the error property. 


# Usage
section intentionlly left empty

## Business Logic
section intentionlly left empty

### Calculate Upside / Downside Percent
section intentionlly left empty

**Validation Logic**
If more that 10 symbols are passed to either method, raise an error "exceeded maximum of 10 symbols per request".

**Exceptions**
If an exception is raised by the underlying adapter, it should be captured in the errors property in the above JSON structure.

**Testing**

- Create a separate test file “test_company_service.py” in the SDK Test directory. 
- Include two tests. 
  - One to handle get_profile() for NVDA
  - One to handle get_summary() for NVDA,META,AAPL,IBM
- Add a docstring on top of the file with the syntax for running the test.







