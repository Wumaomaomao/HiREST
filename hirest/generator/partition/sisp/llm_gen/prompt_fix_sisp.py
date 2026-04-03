PROMPT_FIX= """

Your current task is to supplement the missing single parameter input space based on the existing single parameter space template format and parameter information.

The inputs are INPUT1 INPUT2、INPUT3:
    - INPUI1: The existing single parameter input space template.
    - INPUT2: The missing parameter list that you need to supple.
    - INPUT3: The information of parameters in the swagger file.

# Step

1. Generate the single parameter input space of missing parameter:
    - You need to check the missing parameters provided in INPUT2 and observe the swagger file fragment provided in INPUT3 to generate a single parameter input space.
    - To achieve this, consider the following:
        1. **Identify Diverse Input Scenarios as more as possible**: Explore a wide range of input scenarios that encompass different use cases by analyzing variable names, types, and descriptions. Pay particular attention to the following semantic categorization and design rules:
            - **Semantic Variants** : Identify whether variables within the same semantic category can be subdivided into meaningful variants. For example, language codes might include standard codes (en, fr) and regional variants (en-US, fr-CA) based on functionality or region-specific behavior.
            - **Hierarchical Classification** : Determine whether variables can be classified into secondary or tertiary types. For instance, operators could be categorized into binary (e.g., add) and ternary operators, while status codes might be divided into informational, success, redirection, client error, and server error types.
            - **Contextual Subcategories** : Explore input categorizations that are influenced by application-specific contexts. For example, age groups in a ticketing system might be divided into children, teenagers, adults, and seniors, reflecting functional distinctions.
            - **Environment and Locale Effects**: Incorporate inputs that reflect different environments or locales, such as different time zones, currency formats, or measurement systems. For example, a date format might differ (MM/DD/YYYY in the US versus DD/MM/YYYY in Europe).
        2. **Examine Edge Cases and Boundaries**: Focus on the boundaries of input parameters and explore edge cases that may not be immediately obvious. This includes values at the limits of acceptable ranges and inputs that might lead to exceptions or error, such as:
            - **Format Errors**: Inputs that deviate from expected formats.
            - **Type Errors**: Inputs that are of the wrong data type
            - **Semantic Errors**:  Inputs that violate business rules, even though they might pass format and type checks. 
            - **Extreme Values**: such as the maximal and minimal values for numerical parameters.
            - **Null Inputs**:  Explore cases where required inputs are null.
            - **Unexpected Inputs**: Use your imagination to create unexpected input values.
        3. **Define Input Space Categories**: 
            - When partitioning the input space, categorize the inputs into distinct types. For each category, provide a clear format and a set of example values. This will help ensure a systematic exploration of diverse input scenarios.
        4. **Document Input Categories**: 
            - For each category, describe the format and provide **as many representative samples as possible**. Ensure that both valid and invalid categories are covered.
        5. **Mandatory <MISS_KEY> Category**:
            - You must include `<MISS_KEY>` as an `input_space_category` based on `required`:
                - If `required` is `true`: put `<MISS_KEY>` in `invalid_input_space_categories`.
                - If `required` is `false`: put `<MISS_KEY>` in `valid_input_space_categories`.
2. Follow format:
    - You need to observe the format of INPUT1 and output it accordingly.
    
** Output Format: **

Please respond with only the JSON list, no explanation or extra comments.

[
    {
        "parameter_name": "text",
        "type": "string",
        "required": false,
        "format": [
            ...
        ],
        "valid_input_space_categories": [
            {
                "input_space_category": "Short Text",
                "description": "A short text input for quick grammar checks.",
                "representative_samples": [
                    "Hello world!",
                    "This is a test."
                ]
            }
            ...
        ],
        "invalid_input_space_categories": [
            {
                "input_space_category": "Empty String",
                "description": "An empty string input.",
                "representative_samples": [
                    ""
                ]
            },
            ...
        ],
        "operationId": null,
        "url_path": "/check",
        "http_verb": "post"
    },
    ...
]
""".strip()