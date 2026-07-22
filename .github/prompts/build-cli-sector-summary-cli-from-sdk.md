Build cli sector summary from sdk

Context:
- Application Architecture:   docs/sdk-architecture.md
- CLI Architecture:     		  docs/cli/architecture.md
- SDK Design:             		docs/sdk-architecture.md
- Exception Handling:     		docs/exception-handling.md
- CLI tools of choice:    		Typer and Rich
- Pytest test folder:		      /test/cli
- testing documentation:  	  /docs/cli//testing-documentation.md
- usage  documentation:  	    /docs/cli/usage-documentation.md

You are a python CLI developer with knowledge using Typer and Rich.  Import the sector summary SDK and create a sector summary CLI that allows executing the  following sample command variations:

mi sector summary  
mi sector summary –periods 1D
	mI sector summary –periods 1D,2W
	mI sector summary –periods 2W –symbols XLK,XLE,XLU

Use the following as supported periodCodes:
1D (for today)
2W, 1M, 3M  (for 2 week, 1 month, and 3 month)
6M, YTD, 1Y, 3Y, 5Y (translates to  6m, Year to date, 1 year, 3 year and 5 year)



Constraints: Create CLI using the SDK service found in this path:
 src/mi_sdk/services/sector_summary_service.py

The CLI should leverage the same exception hierarchy as the SDK

Generate Pytest for the sector summary  CLI in the /tests/cli  folder

When done, update testing documentation, located in /docs/cli/testing-documentation.md,
with description of exact syntax on how to test the sector summary cli.

Update the usage documentation, located in /docs/cli/usage-documentation.md, with instructions on how to use the CLI

