Build RiskRewardProfile SDK service

## Preamble

Before moving forward stop here and read the **pre-execution review** document located in this file: 
```code
.github/prompts/prompt_templates/pre-execution-extensive-review.md 
```
and then we can proceed with the prompt below as directed. 

## Role and Objective

You are a Python SDK developer that has been asked to create a service that provides a RiskRewardProfile for a given company. 
- Create a risk reward  profile service SDK in a separate file called risk_reward_profile_service.py. 

### SDK Class to be created
- **Create Class** RiskRewardProfile in **file** risk_reward_profile.py file, 

### SDK Class Methods to be created
- **Method:** get_analyst_targets() 
  - **Description** - calls the get_targets method in the SDK analyst_service.py file
  - **Inputs**: A stock symbol or list of stock symbols, upto 10 symbols maximum.
  - **Response**: it will return the JSON from the get_targets method. 
  
- **Method:** get_current_price() 
  - **Description** uses the JSON returned from get_profile method in the company_profile SDK service to obtain the current stock price for a given company or list of companies.
  - **Inputs**: A stock symbol or list of stock symbols, upto 10 symbols maximum.
  - **Response**: the method will modify response from getProfile to return the following response JSON structure. 
  ```json
  [{"symbol": NVDA, "price":270}, {"symbol": CLSK, "price":33}]
  ```
- **Method:** calc_upside_downside_pct()
  - **Description** uses two of the class methods to calculate upside and downside percent.  
    - **method1**: get_current_price() method used to get current price.
    - **method2**: get_analyst_targets() method to get price targets
  - **Business Logic**: refer to Business Logic section withing this prompt
  - **Inputs**: A stock symbol or list of stock symbols, upto 10 symbols maximum.
  - **Response**: return the following response JSON structure. 
  ```json
  [
   {"symbol": NVDA, "upsidePct":22.0, "downsidePct": 12.0 }, 
   {"symbol": CLSK, "upsidePct":12.0, "downsidePct": 05.0 }
  ]
  ```
- **Method:** is_price_below_target_low()
  - **Description** uses two class methods to determine if price is below target.
    - **method1**: get_current_price() method used to get current price.
    - **method2**: get_analyst_targets() method to the low target
  - **Business Logic** uses price from get_current_price() and low from get_analyst_targets to return true if current price is below low target and false if not.  
  - **Inputs**: A stock symbol or list of stock symbols, upto 10 symbols maximum.
  - **Response**: return the following JSON structure. 
  ```json
  [
   {"symbol": NVDA, "priceBelowTargetLow": true, "targetLowUpsidePct": 45.0},
   {"symbol": CLSK, "priceBelowTargetLow": false, "targetLowUpsidePct": 45.0}
  ]
  ```
- **Method:** get_reward_risk_ratio()
  - **Description** This service will return 0.0 as placeholder until implemented
    - **method1**: TBD
    - **method2**: TBD
  - **Business Logic** 
  - **Inputs**: A stock symbol or list of stock symbols, upto 10 symbols maximum.
  - **Response**: return the following JSON structure. 
 ```json
 {
  "entryPrice": 14.47,
  "targetPrice": 23.96,
  "stopLossPrice": 12.00,
  "stopLossMethod": "technical_support",
  "rewardRiskRatio": 3.84
}
```

- **Method:** get_risk_reward_profile()
  - **Description** This service will build the JSON object to 
    - **method1**: TBD
    - **method2**: TBD
  - **Business Logic** 
  - **Implementation Logic** refer to the Implementation Details section in this prompt 
  - **Inputs**: A stock symbol or list of stock symbols, upto 10 symbols maximum.
  - **Response**: return the following JSON structure:
```json
[
  {
    "symbol": "CLSK",
    "currentPrice": 14.47,
    "targetConsensus": 23.96,
    "targetHigh": 27.00,
    "targetLow": 21.00,
    "upsidePct": 65.58,
    "downsidePct": 65.58,
    "outlook": "upside",
    "priceBelowTargetLow": true,
    "rewardRiskRatio": 0.0
  },
  {
    "symbol": "IMB",
    "currentPrice": 14.47,
    "targetConsensus": 23.96,
    "targetHigh": 27.00,
    "targetLow": 21.00,
    "upsidePct": 65.58,
    "downsidePct": 65.58,
    "outlook": "upside",
    "priceBelowTargetLow": true,
    "rewardRiskRatio": 0.0
  }
]
``` 


**Context:**
- Architecture:       	docs/sdk-architecture.md
- SDK Design:        	  docs/sdk-architecture.md
- Exception Handling:	docs/exception-handling.md
- SDK Services Directory  src/mi_sdk/services
- FMP providers Directory  src/mi_sdk/providers/fmp
- FMP analyst provider  fmp_analyst.py 


**Constraints:**
- Must follow .github/copilot-instructions.md
- Must not expose provider-specific logic in the SDK service


**Sample JSON response for get_consensus**
```json
{
  "consensus": [
    {
      "symbol": "NVDA",
      "strongBuy": 2,
      "buy": 58,
      "hold": 16,
      "sell": 3,
      "strongSell": 0,
      "recommendation": "buy"
    },
    {
      "symbol": "AAPL",
      "strongBuy": 2,
      "buy": 58,
      "hold": 16,
      "sell": 3,
      "strongSell": 0,
      "recommendation": "buy"
    }
  ],
  “errors”: [
	  <capture errors/exceptions here>
  ]
}
```

**Sample JSON response for get_targets**
```json
{
  "priceTargets": [
    {
      "symbol": "NVDA",
      "high": 400.0,
      "low": 245.0,
      "median": 360.0,
      "consensus": 339.35
    },
    {
      "symbol": "AAPL",
      "priceTarget": {
        "high": 400.0,
        "low": 245.0,
        "median": 360.0,
        "consensus": 339.35
      }
    }
  ],
  “errors”: [
	  <this will show the errors that were raised fmp_analyst adapter>
  ]
}
```

## Implementation Details

## use Asyncio for get_risk_reward_profile() method
The get_risk_reward_profile() method will need to call several services. For efficiency, 
run the various methods in parallel using an AsyncPipeLine.
The methods that a symbol or list of symbols as a parameter,  can all run in parallel as they all will be passed the same parameter list. Below is a generic example of an AsyncPipeLine.
```python
import asyncio


class AsyncPipeline:

    async def step_one(self):
        await asyncio.sleep(1)
        return "Step 1 complete"

    async def step_two(self):
        await asyncio.sleep(1)
        return "Step 2 complete"

    async def run_all(self):
        # Runs both async methods concurrently
        results = await asyncio.gather(self.step_one(), self.step_two())
        return results


# Usage
pipeline = AsyncPipeline()
results = asyncio.run(pipeline.run_all())
outputJson = mapResultsToOutPutJson()
print(outputJson)
```
Use a similar approach for the get_get_risk_reward_profile().
These are the services that should run in parallel.
- get_analyst_targets() 
- get_current_price()
- get_reward_risk_ratio()
- get_stop_loss_price()


## Business Logic

### Calculate Upside / Downside Percent

Below are samples of JSON inputs

#### price_targets JSON
```json
  "priceTargets": [
    {
      "symbol": "NVDA",
      "high": 515,
      "low": 270,
      "median": 322.5,
      "consensus": 345.21
    }
  ],
  "errors": []
}
```

#### company price JSON
```json
 [{"symbol": NVDA, "price":270}, {"symbol": CLSK, "price":33}]
```

Given the two inputs above, provide the calculation for updside percent and downside percent that will be used to populate updsidePct and downsidePct in a JSON structure like below. Use current price and targetConsensus and targetLow price as the basis for the calculation.
```json
{
  "symbol": "CLSK",
  "currentPrice": 14.47,
  "targetConsensus": 23.96,
  "targetHigh": 27.00,
  "targetLow": 21.00,
  "upsidePct": ,
  "downsidePct": ,
  "outlook": "upside",
  "priceBelowTargetLow": true
}
```

**Validation Logic**
If more that 10 symbols are passed to either method, raise an error "exceeded maximum of 10 symbols per request".

**Exceptions**
If an exception is raised by the underlying adapter, they should be captured in the errors property in the above JSON structure.

**Testing**

- Create a separate test file “test_risk_reward_profile.py” in the SDK Test directory. 
- Include two tests. 
  - One to handle get_risk_reward_profile for NVDA
  - One to handle get_risk_reward_profile for NVDA,META,AAPL,IBM
- Add a docstring on top of the file with the syntax for running the test.







