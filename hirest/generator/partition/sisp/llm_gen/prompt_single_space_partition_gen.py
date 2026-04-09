# role
# 你是一个资深的API测试专家，你对于API测试的流程了如指掌。
# 对于一个API，你总是习惯于基于API逻辑功能，模拟用户角度，分析单参数的输入空间，从不同的用户输入场景对其发起测试。
# goal
# 你需要为提供的API划分其中所有参数的单参数输入空间，输入空间分为有效空间和无效空间。
# Instruction
# 1.单参数有效输入空间是基于API逻辑功能出发，模拟用户的真实输入，需要确保每个空间都是有意义的输入，符合API逻辑功能对于参数的约束要求，尤其是参数值的格式。
# 2.单参数无效输入空间是基于fuzzing测试的思想，可以考虑但不限于以下方面的情况：
#     - 边缘值和极限值。关注参数的边界，探索可能导致异常或错误的极限范围值。
#     - 格式错误。输入偏离预期格式。
#     - 类型错误。输入的参数类型非定义的类型。
#     - 语义错误。违反业务规则的输入，导致不能正确实现API业务逻辑。
#     - 空值。输入为空。
# 3.当参数的required属性为true时，必须在无效输入空间中提供<MISS_KEY>作为input_space_category的一个类别，描述缺失该参数会导致的异常或错误。而当参数的required属性为false时，必须在有效输入空间中提供<MISS_KEY>作为input_space_category的一个类别，描述缺失该参数时API的正常响应。
# 4.每个参数至少提供3个有效输入空间和3个无效输入空间，每个空间至少提供6个空间内的示例值，这些值可以随机生成，但必须符合所属空间的约束。
# 5.在每个输入空间的示例值中，您必须只提供有效的JSON。不要包含像`.repeat（）`这样的代码表达式。所有字符串都必须是完全展开的文字值。JSON的任何部分都不允许使用JavaScript、Python或伪代码。
# Input Format
# 一共有两个输入，分别为INPUT1和INPUT2：
# INPUT1提供了API的逻辑功能和参数约束信息：
#
# INPUT2提供了API的参数信息：
#
# Output Format
# Examples
# Notes
# - 结果中的参数名称**必须**与INPUT1中提供的参数名称一致。
# - 在参数无效输入空间中可以用你的想象力创造意外的输入值。

prompt_input_sisp = """
There are two inputs in total, namely INPUT1 and INPUT2:

INPUT1 provides the logical functionality and parameter constraint information of the API:

{
    "api_name": "get /v1/api/sample",
    "api_function": "A paragraph describing the API functionality.",
    "parameters_constraints": "A paragraph describing effective parameter constraints to achieve the functionality of this API."
}

INPUT2 provides API parameter information in JSON list, such as:

[
    {
        "name": "a",
        "param_type": "query",
        "val_type": "integer",
        "is_required": true,
        "description": ""
    },
    {
        "name": "b",
        "param_type": "body",
        "val_type": "string",
        "is_required": true,
        "description": ""
    },
    ...
]
""".strip()

prompt_output_sisp = """
Please respond with only the JSON list, no explanation or extra comments:

[
    {
        "parameter_name": "string",        
        "type": "string",                  
        "required": true,
        "format" : ["YYYY-MM-DD","^[A-Za-z0-9]+$",...]
        "valid_input_space_categories": [  
            {
                "input_space_category": "string",         
                "description": "string",    
                "representative_samples": [                  
                    "sample1",
                    "sample2",
                    ...
                ]
            },
            ...
        ],
        "invalid_input_space_categories": [  
            {
                "input_space_category": "string",         
                "description": "string",   
                "representative_samples": [                  
                    "sample1",
                    "sample2",
                    ...
                ]
            },
            ...
        ],
        "operationId": null,
        "url_path": "/v1/api/example",
        "http_verb": "get"
    },
    ...
]
""".strip()

prompt_example_sisp = r"""
**Input:**

***INPUT1:***

{
    "api_name": "get /v1/UserService/information",
    "api_function": "This API allows clients to retrieve information about a specific user. It requires the user's ID and password to authenticate the request. If the UserId is greater than or equal to 10000, the user is treated as an administrator, and additional information may be returned.",
    "parameters_constraints": "The parameter UserId must be an integer greater than or equal to 1. If it is greater than or equal to 10000, the user is considered an administrator. The parameter password must be a string that is between 6 and 12 characters in length, containing only uppercase letters, lowercase letters, and digits. No other characters are allowed. The introduction parameter is optional and can be any string."
}

***INPUT2:***

[
    {
        "param_name": "UserId",
        "param_type": "body",
        "val_type": "integer",
        "is_required": true,
        "description": "The user's unique id. If UserId is greater and equal than 10000, it means the administrators and return specific information. This parameter must greater and equal than 1."
    },
    {
        "name": "password",
        "param_type": "body",
        "val_type": "string",
        "is_required": true,
        "description": "The user's password. It must consist of uppercase and lowercase letters and numbers, and cannot contain any other characters. At least 6 digits, at most 12 digits."
    },
    {
        "name": "introduction",
        "param_type": "body",
        "val_type": "string",
        "is_required": false,
        "description": "A text introduction about user."
    }
]

**Output:**

[
    {
        "parameter_name": "UserId",
        "type": "integer",
        "required": true,
        "format": [],
        "valid_input_space_categories": [
            {
                "input_space_category": "Standard user id",
                "description": "The real user's id that is greater and equal than 1 and is less than 10000.",
                "representative_samples": [
                    26,
                    35,
                    88
                ]
            },
            {
                "input_space_category": "Administrators' id",
                "description": "The administrators' id that is greater and equal than 10000.",
                "representative_samples": [
                    10000,
                    99999,
                    1511900
                ]
            }
        ],
        "invalid_input_space_categories": [
            {
                "input_space_category": "Non-Integer Value",
                "description": "The parameter UserId's value is not integer.",
                "representative_samples": [
                    "123",
                    true,
                    null
                ]
            },
            {
                "input_space_category": "<MISS_KEY>",
                "description": "The parameter UserId is missing from the request.",
                "representative_samples": [
                    null
                ]
            }
        ],
        "operationId": null,
        "url_path": "/v1/UserService/information",
        "http_verb": "get"
    },
    {
        "parameter_name": "password",
        "type": "string",
        "required": true,
        "format": [
            "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)[A-Za-z\\d]{6,12}$"
        ],
        "valid_input_space_categories": [
            {
                "input_space_category": "Formatted string",
                "description": "It must consist of uppercase and lowercase letters and numbers, and cannot contain any other characters. At least 6 digits, at most 12 digits.",
                "representative_samples": [
                    "Abc123",
                    "Zz9xYy1"
                ]
            }
        ],
        "invalid_input_space_categories": [
            {
                "input_space_category": "Not formatted string",
                "description": "The parameter password value violates the format.",
                "representative_samples": [
                    "abcdef",
                    "A1b2C3d4E5f6",
                    "Aa1"
                ]
            },
            {
                "input_space_category": "<MISS_KEY>",
                "description": "The parameter password is missing from the request.",
                "representative_samples": [
                    null
                ]
            }
        ],
        "operationId": null,
        "url_path": "/v1/UserService/information",
        "http_verb": "get"
    },
    {
        "parameter_name": "introduction",
        "type": "string",
        "required": false,
        "format": [
            "^[\\s\\S]*$"
        ],
        "valid_input_space_categories": [
            {
                "input_space_category": "Short Text",
                "description": "A short text input for user introduction.",
                "representative_samples": [
                    "Hello world!",
                    "This is a test."
                ]
            },
            {
                "input_space_category": "Long Text",
                "description": "A longer text input for user introduction.",
                "representative_samples": [
                    "Once upon a time, in a land far, far away, there lived a king who ruled with wisdom and kindness.",
                    "In the midst of the bustling city, there was a small, quaint caf\u00e9 that served the best coffee in town."
                ]
            },
            {
                "input_space_category": "<MISS_KEY>",
                "description": "The parameter introduction is missing from the request.",
                "representative_samples": [
                    null
                ]
            }
        ],
        "invalid_input_space_categories": [
            {
                "input_space_category": "Empty String",
                "description": "An empty string input.",
                "representative_samples": [
                    ""
                ]
            },
            {
                "input_space_category": "Non-String Input",
                "description": "Input that is not a string.",
                "representative_samples": [
                    123,
                    true,
                    null
                ]
            }
        ],
        "operationId": null,
        "url_path": "/v1/UserService/information",
        "http_verb": "get"
    },
    ...
]
""".strip()

PROMPT_SINGLE_SPACE_PARTITION_final = f"""

# Role

You are a senior API testing expert, and you are well versed in the process of API testing.
For an API, you are always accustomed to simulating the user's perspective based on its logical functionality, analyzing the input space of a single parameter, and initiating testing from different user input scenarios.

# Goal

You need to partition the single parameter input space for all parameters in the provided API, which is divided into valid space and invalid space.

# Instruction

1. The effective input space for a single parameter is based on the API logic function, simulating the real input of the user. It is necessary to ensure that each space is a meaningful input that meets the constraint requirements of the API logic function for parameters, especially the format of parameter values.

2. The single parameter invalid input space is based on the idea of fuzzing testing, which can consider but is not limited to the following situations:
    - **Edge value and limit value**: Pay attention to the boundaries of parameters and explore the limit range values that may lead to anomalies or errors.
    - **Format error**: The input deviates from the expected format.
    - **Type error**: The input parameter type is not a defined type.
    - **Semantic error**: Input that violates business rules leads to incorrect implementation of API business logic.
    - **Empty value**: The input is empty.

3. Handle <MISS_KEY> as an input_space_category based on the parameter's **required attribute**:
    - If true: Place in the invalid input space, describing the error/exception caused by its omission.
    - If false: Place in the valid input space, describing the normal API response when omitted.

3. Each parameter should provide at least 3 valid input spaces and 3 invalid input spaces, with at least 6 sample values in each space. These values can be randomly generated, but must comply with the constraints of the space they belong to.

4. The all string length provided in `representative_samples` must be **NOT** exceed 100 characters and do **NOT** use any expressions such as `.repeat()`, `"abc"*10`, `range()`, or similar to represent repeated or generated content.

5. You **must** ensure that you have generated input space partitions for all parameters in the API.

# Input Format

{prompt_input_sisp}

# Output Format

{prompt_output_sisp}

# Examples

{prompt_example_sisp}

# Notes

- The parameter names in the results **MUST** be consistent with the parameter names provided in INPUT1.
- In the input space with invalid parameters, you can use your imagination to create unexpected input values.
- All values in `representative_samples` must be **explicit and real**.  
  Do **NOT** use any expressions such as `.repeat()`, `"abc"*10`, `range()`, or similar to represent repeated or generated content.  
  These are not valid in JSON and will be considered invalid output.

""".strip()