
## use AsyncPipeline for methods 
When you need to call several services and/or methods in parallel for efficiency, or call the same service with different parameters in parallel, use an AsyncPipeLine.
The methods can all run in parallel and get aggregated once they all have completed.
Below is a generic example of an AsyncPipeLine.
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

Provide the method that the construct the Asyncio process and the list of methods you would like to run in parallel.
Use a similar approach for the get_get_risk_reward_profile().
These are the services that should run in parallel.
- get_analyst_targets() 
- get_current_price()
- get_reward_risk_ratio()
- get_stop_loss_price()
