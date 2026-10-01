Add Historical prices to Company SDK service

## Preamble

Before moving forward stop here and read the **pre-execution review** document located in this file: 
```code
.github/prompts/_prompt_templates/pre-execution-basic-review.md 
```
and then we can proceed with the prompt below as directed. 

## Role and Objective

You are a Python SDK developer that has been asked to create a service that returns a  company's historical prices data using the get_historical_pricing method in the fmp-company.py provider.
- Add a get_historical_pricing method to the existing SDK file called company_service.py. 

### SDK Class to be updated
- **Update Class** CompanyService in **file** company_service.py file

### SDK Class Methods to be created
- **Method:** get_historical_pricing() 
  - **Description** - returns daily prices data for a particular date range.
  - **Inputs**: A stock symbol, from_date, to_date or stock sybmol and lookback_period
  - **Response**: is a modified version of the JSON from the get_historical_pricing method, where "data" property will be renamed to "priceData", and the error property will be added at the end.
  
 
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

**Sample JSON response for get_historical_pricing()**
```json
{
  "requestedTradingDays": 3,
  "priceData": [
    {
      "symbol": "TER",
      "date": "2026-04-01",
      "open": 301.97,
      "high": 316.81,
      "low": 300.3,
      "close": 312.2,
      "volume": 2961800,
      "change": 10.23,
      "changePercent": 3.39,
      "vwap": 307.82
    },
    {
      "symbol": "TER",
      "date": "2026-03-31",
      "open": 278.3,
      "high": 297.39,
      "low": 277.93,
      "close": 296.46,
      "volume": 3354000,
      "change": 18.16,
      "changePercent": 6.53,
      "vwap": 287.52
    },
    {
      "symbol": "TER",
      "date": "2026-03-30",
      "open": 301,
      "high": 301,
      "low": 273.07,
      "close": 276.35,
      "volume": 3130127,
      "change": -24.65,
      "changePercent": -8.19,
      "vwap": 287.855
    },
    {
      "symbol": "TER",
      "date": "2026-03-26",
      "open": 314.98,
      "high": 314.98,
      "low": 296.67,
      "close": 297.34,
      "volume": 3017610,
      "change": -17.64,
      "changePercent": -5.6,
      "vwap": 305.9925
    },
    ...
  ],
   "errors": [
    ...
  ],
}
```

## Implementation Details**
The get_historical_pricing() method parameters will support two modes for defining date range
1) A stock symbol, along with from_date and to_date 
2) A stock sybmol and a lookback_period
   
The expected format of the from_date and the to_date is YYYY-MM-DD

- **For mode 1**, the from_date and to_date can be passed to the FMP provider get_historical_pricing() method as-is.

- **For mode 2**, the to_date will default to curent date and the from_date is calculated based on the lookback_period. 

Use the following as supported periodCodes: 
- 1D, 2D, 3D, 4D, 5D (1D for today, 2D for 2 days, 3D for 3days, 4D for 4 days)
- 1W, 2W, 1M, 3M, 6M, 9M, 12M, 18M  (for 1 week, 2 week, 1 month, and 3 month)
- 1Y, 2Y, 3Y, 4Y, 5Y (translates to  1 Year,  2 year, 3 year, 4 year, and 5 year)

Create a separate method that converts the periodCode and returns the from_date as YYYY-MM-DD, that is required by the FMP provider. Sample method name below:
```code
 convert_periodCode_to_from_date(periodCode)
```
Update the JSON property "requestedTradingDays" with the number elements in the priceData array. If priceData has 10 pricing data entries, set "requestedTradingDays" to 10.


# Usage
section intentionlly left empty

## Business Logic
section intentionlly left empty

## Validation Logic
If lookback_period does not match any of the supported periodCodes, raise validation error

## Exceptions
Have the Company SDK employ the Exception handling pattern for SDK services, that is documented in file 
```code .github/prompts/exception_management/exception_management.md.```

## Testing

- Update test file “test_company_service.py” in the SDK Test directory. 
- Include two tests. 
  - One to handle get_historical_pricing() for IBM with lookback period of 1M.
  - One to handle get_historical_pricing() for CSCO with from_date of 2026-08-30 and to_date of 2026-09-30.
- Add a docstring on top of the file with the syntax for running the test either in gitbash or windows powershell.







