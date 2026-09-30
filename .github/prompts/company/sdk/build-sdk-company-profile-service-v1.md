Build Company SDK service

## Preamble

Before moving forward stop here and read the **pre-execution review** document located in this file: 
```code
.github/prompts/_prompt_templates/pre-execution-basic-review.md 
```
and then we can proceed with the prompt below as directed. 

## Role and Objective

You are a Python SDK developer that has been asked to create a service that returns a company profile using the fmp-company.py provider.
- Create a company service SDK in a separate file called company_service.py. 

### SDK Class to be created
- **Create Class** CompanyService in **file** company_service.py file

### SDK Class Methods to be created
- **Method:** get_profile() 
  - **Description** - calls the get_profile method in the SDK fmp_company.py file
  - **Inputs**: A stock symbol or list of stock symbols, upto 10 symbols maximum.
  - **Response**: it will modify the JSON from the get_profile method by assigning the array to the property "companies", and adding the error property at the end.
  
- **Method:** get_summary() 
  - **Description** calls the get_profile method in the SDK fmp_company.py file and returns a subset of the fields listed in the output of the get_profile() method response. 
  - **Inputs**: A stock symbol or list of stock symbols, upto 10 symbols maximum.
  - **Response**: the method will modify the JSON response from get_profile to align with the sample JSON provided in the section 'Sample JSON response for get_summary()'.
  
**Context:**
- Architecture:       	.github/copilot-instructions.md
- SDK Design:        	  .github/copilot-instructions.md
- Exception Handling:	 .github/prompts/exception_management/exception_management.md
- SDK Services Directory  src/mi_sdk/services
- SDK Test Directory    tests/sdk
- FMP providers Directory  src/mi_sdk/providers/fmp
- FMP company provider  fmp_company.py 

## Constraints:
- Must follow .github/copilot-instructions.md
- Must not expose provider-specific logic in the SDK service

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

**Sample JSON response for get_profile()**
```json
{
  "companies": [
    {
    "symbol": "NVDA",
    "price": 228.87,
    "marketCap": 5543460270000,
    "beta": 2.217,
    "lastDividend": 0.28,
    "range": "164.27-236.54",
    "change": 1.49,
    "changePercentage": 0.65529,
    "volume": 93296546,
    "averageVolume": 141713674,
    "companyName": "NVIDIA Corporation",
    "currency": "USD",
    "cik": "0001045810",
    "isin": "US67066G1040",
    "cusip": "67066G104",
    "exchangeFullName": "NASDAQ Global Select",
    "exchange": "NASDAQ",
    "industry": "Semiconductors",
    "website": "https://www.nvidia.com",
    "description": "NVIDIA Corporation stands as a prominent provider of advanced graphics, computational, and networking solutions, operating across the United States, Taiwan, China, and numerous international markets",
    "ceo": "Jensen Huang",
    "sector": "Technology",
    "country": "US",
    "fullTimeEmployees": "42000",
    "phone": "408 486 2000",
    "address": "2788 San Tomas Expressway",
    "city": "Santa Clara",
    "state": "CA",
    "zip": "95051",
    "image": "https://images.financialmodelingprep.com/symbol/NVDA.png",
    "ipoDate": "1999-01-22",
    "defaultImage": false,
    "isEtf": false,
    "isActivelyTrading": true,
    "isAdr": false,
    "isFund": false
    }
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
Since the get_profile method in the fmp_company.py provider only supports a single symbol parameter, in this SDK implement the ability to accept multiple symbols and call the respective fmp_company adapter method for each symbol in parallel. Wait until all method calls are completed for each symbol. Get the overall response for each symbol, map the companyName to  name in the get_summary() JSON result, and return all responses at once using the JSON response provided in the Sample JSON response section above, for get_profile(). If a call failed for one or two symbols, refer to the section in this document called "Exceptions".


# Usage
section intentionlly left empty

## Business Logic
section intentionlly left empty

## Validation Logic
If more than 10 symbols are passed to either method, raise an error "exceeded maximum of 10 symbols per request".

## Exceptions
Have the Company SDK employ the Exception handling pattern for SDK services, that is documented in file 
```code .github/prompts/exception_management/exception_management.md.```

## Testing

- Create a separate test file “test_company_service.py” in the SDK Test directory. 
- Include six tests. 
  - One to handle get_profile() for IBM
  - One to handle get_profile() for NVDA, META
  - One to handle get_profile() with no symbols provided
  - One to handle get_summary() for IBM
  - One to handle get_summary() for NVDA,META,AAPL,IBM,AVGO
  - One to handle get_summary() with no symbols provided
- Add a docstring on top of the file with the syntax for running the test.







