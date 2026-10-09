# Add method to the MarketInsights Stack

## Prompt Generation Instructions.

You are a prompt file generator. 

You are going to generate prompt markdown files using the instructions in this prompt.

There are three  different config parameter sections int this prompt.
One for the Provider, one for the SDK, and one for the FASTAPI.

This is the process for generating prompt files for Provider, SDK, and FASTAPI.

- Read the specific Config parameters  (eg Provider, SDK, FASTAPI) in this prompt
- Read the the specific template file provided. 
- Replace the config parameter names in angle brackets < > within the template file, with the values in the specific Config Parameters. When value is substituted, the angle brackets can be removed.
- Save the modified template file to the designated location.

Not all values in angle brackets <> may have substitution values in the generated prompt files. For files with angle brackets that were not substituted, let me know when you're done generating all files, which file still has <> brackets so I can review and update manually.


# Step(1) Remove all comments from prompt; 
You will see comments in this document intended for the user running this prompt.  
It will use comment start delimeter of /* and  end delimeter of */. The start  delimeter can begin on one line
and span multiple lines before the encountering the end delimeter.
As the first step, remove  all comments before running the prompt.

# Step(2) Generate the Provider Prompt file

## Provider file generation parameters

See "Provider Config Parameters" section in this prompt.

Below is template input file and where to save the generated output prompt file.

- **Input template file**:  .github/prompt_templates/provider_templates/add_method_to_provider_template.md
- **Output template file**: .github/prompts/<domain-folder-name>/<generated-prompt-file-name>

# Step(3) Generate the SDK Prompt file

See "SDK Config Parameters" section in this prompt.

Below is template input file and where to save the generated output prompt file.

- **Input template file**:  .github/prompt_templates/provider_templates/add_method_to_provider_template.md
- **Output template file**: .github/prompts/<domain-folder-name>/<generated-prompt-file-name>

# Step(4) Generate the FAST Prompt file

See "FASTAPI Config Parameters" section in this prompt.

Below is template input file and where to save the generated output prompt file.

- **Input template file**:  .github/prompt_templates/api_templates/add_method_to_api_template.md
- **Output template file**: .github/prompts/<domain-folder-name>/<generated-prompt-file-name>

## Provider Config Parameters
<pre>
domain-name:                           /* Examples: Sector, Company */
provider-method-name1:
provider-method-description1:
provider-input-names1:
provider-optional-method-comment1-flag: yes | no
provider-optional-method-comment1: "no comment"
provider-method-name1-endpoint: 
</pre>

/* The sdk-service-name is used for sdk file creation. If sdk method is complicated, I maintain it in a separate 
  file. For example, if sector leadership and sector performance are large and complicated, hence I keep them in 2 sdk files. The files would be sector_leadership_service.py and sector_performance_service.py.
  If they are simple services like, company profile and company stock_quote, I keep them in one sdk file and add the two methods (get_profile, get_stock_quote) to the one sdk file company_service.py file  */

## SDK Config Parameters
<pre>
domain-name:
sdk-service-name:                     /* Examples: sector_leadership, sector_summary */
sdk-method-name1:
sdk-method-description1:
sdk-input-names1:
sdk-optional-method-comment1-flag: yes | no  /* add comment if makes the  purpose of method clearer */
sdk-optional-method-comment1: "no comment"
sdkSupportsMultiSymbolRequests: yes | no
PropsWithPrecisionGT2: yes | no
higherPrecisionProperties: [ 
                            { "property-name1": "precision1": 2, }, 
                            { "property-name2": "precision2": 2 } 
                         ]
</pre>

## FASTAPI Config Parameters
<pre>
domain-name:                     /* Examples:  Sector, Company */
sub-domain-name:                 /* Examples:  summary (as in sector_summary), profile (as in company_profile) */  
sdk-service-filename:
sdk-method-name1:                /* method name in the SDK called by the FASTAPI */
fastapi-method-name1:
fastapi-method-description1:
fastapi-input-names1:
</pre>

