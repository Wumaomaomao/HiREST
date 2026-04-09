#
# Role
# 你是一位精通软件测试的专家，你最擅长使用黑盒测试中的等价类划分来生成测试用例，从而覆盖更广的用户输入情况。
# Goal
# 你现在要基于API参数之间的约束关系，对一个API进行约束空间的划分，以便后续某次测试可以选择不同的约束空间后生成不同场景的测试用例。
# Instruction
# 1.每个约束空间(除了第一个和最后一个）根据某条参数之间的约束关系唯一确定。
# 2.一个API中的所有约束空间以“space1”，“space2”，“space3”，。。。，“spaceN”（N>=2）表示，每个约束空间中包含以下内容：
#     - involved-parameters：该约束空间涉及的参数。即该约束空间满足或违反父空间约束关系的情况中所有涉及的参数。
#     - subspaceX（X>=1）：满足父空间约束关系的所有情况。
#     - error_spaceX（X>=0）：违反父空间约束关系的所有情况。
# 3.每个subspaceX(X>=1)或error_spaceX(X>=0)包含三项：
#     - parameter: 参数存在性。即该子空间满足或违反父空间约束关系的情况中所有涉及的参数。
#     - parameter-value：参数与值之间的关系。在子空间满足或违反父空间约束关系的情况下，用自然语言描述所有参数与值之间的关系。
#     - parameter-parameter：参数与参数之间的关系。在子空间满足或违反父空间约束关系的情况下，用自然语言描述所有参数与参数之间的关系。
# 4.无论任何API，都必须包含以下两个维度的space：
#     - Minimum input space：该space代表该API的最小（强制）输入参数，该space名字强制定为space1，并且其中只有一个subspace1。
#     - Expandable Parameter Spaces：用于动态加入不涉及任何约束关系的可选参数。对于每个独立的可选参数，你需要为它们独立创建一个space，并且每个space必须且只能包含两个subspace, 其中一个是满足该可选参数存在的subspace，另一个是满足该可选参数不存在的error_space。
# Input Format
# Two JSON inputs, INPUT1 and INPUT2.
# - INPUT1: Contains dependency relationships for parameters in each method of several APIs.
# - INPUT2: Contains specific parameter information for each method of several APIs.
#
# Output Format
# Notes
# - 确保所有依赖关系都准确反映在分区空间中。
# -考虑可能违反依赖关系的子空间，以实现全面的测试覆盖率。
# -只有在基于依赖关系划分的空间中才能存在错误空间，即在最小（强制）输入空间和可扩展输入空间中没有错误空间。
# -必须注意的是，INPUT1中每条消息中“参数值”和“参数参数”之间的两类差异很容易混淆。您需要确认逻辑符号的左侧和右侧是参数还是值。

prompt_input_misp = """
Two JSON inputs, INPUT1 and INPUT2.

INPUT1: Contains all dependency relationships for parameters in the API, such as:

{
    "/path1": {
        "post": {
            "all-dependencies": [
                "Description of dependency 1.",
                "Description of dependency 2."
            ]
        }
    }
}

INPUT2: Provides API parameter information in JSON list, such as:

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
prompt_output_misp = """
The output should be a valid JSON object structured as follows:

{
    "/path1": {
        "post": {
            "space1": {
                "satisfied-dependencies": "Minimum input space.",
                "involved-parameters": [ ... ],
                "subspace1": {
                    "parameter": [ ... ],
                    "parameter-value": [ ... ],
                    "parameter-parameter": [ ... ]
                }
            },
            "space2": {
                "satisfied-dependencies": "Description of dependency 1.",
                "involved-parameters": [ ... ],
                "subspace1": {
                    "parameter": [ ... ],
                    "parameter-value": [ ... ],
                    "parameter-parameter": [ ... ]
                },
                "subspace2": {
                    "parameter": [ ... ],
                    "parameter-value": [ ... ],
                    "parameter-parameter": [ ... ]
                }
                ...
                "error_space": { /* The all list of ERROR space because it violated the dependency relationship */
                    "error_space1": {
                        "parameter": [ ... ],
                        "parameter-value": [ ... ],
                        "parameter-parameter": [ ... ]
                    },
                    "error_space2": { ... },
                    ...
                }
            },
            ...
        }
    }
}
""".strip()

prompt_example_misp = """
**Input:**

***INPUT1:***

{
    "/hello": {
        "post": {
            "all-dependencies": [
                "Either the parameter male or the parameter female is required.",
                "The parameter rule is only available when the parameter sex is set to auto."
            ]
        }
    }
}

***INPUT2:***

[
    {
        "name": "male",
        "param_type": "body",
        "val_type": "string",
        "is_required": false,
        "description": "The male to be checked. This or 'female' is required."
    },
    {
        "name": "female",
        "param_type": "body",
        "val_type": "string",
        "is_required": false,
        "description": ""
    },
    {
        "name": "sex",
        "param_type": "body",
        "val_type": "string",
        "is_required": true,
        "description": ""
    },
    {
        "name": "rule",
        "param_type": "body",
        "val_type": "string",
        "is_required": false,
        "description": "If rule is exist, the parameter sex is set to auto."
    },
    {
        "name": "check",
        "param_type": "body",
        "val_type": "string",
        "is_required": false,
        "description": ""
    }
]

**Output:**

{
    "/hello": {
        "post": {
            "space1": {
                "satisfied-dependencies": "Minimum input space.",
                "involved-parameters": [
                    "sex"
                ],
                "subspace1": {
                    "parameter": [
                        "sex"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": []
                }
            },
            "space2": {
                "satisfied-dependencies": "Either the parameter male or the parameter female is required.",
                "involved-parameters": [
                    "male",
                    "female"
                ],
                "subspace1": {
                    "parameter": [
                        "male"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": []
                },
                "subspace2": {
                    "parameter": [
                        "female"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": []
                },
                "error_space": {
                    "error_space1": {
                        "parameter": [
                            "male",
                            "female"
                        ],
                        "parameter-value": [],
                        "parameter-parameter": []
                    }
                }
            },
            "space3": {
                "satisfied-dependencies": "The parameter rule is only available when the parameter sex is set to auto.",
                "involved-parameters": [
                    "rule",
                    "sex"
                ],
                "subspace1": {
                    "parameter": [
                        "rule"
                    ],
                    "parameter-value": [
                        "sex = auto"
                    ],
                    "parameter-parameter": []
                },
                "error_space": {
                    "error_space1": {
                        "parameter": [
                            "rule"
                        ],
                        "parameter-value": [
                            "sex != auto"
                        ],
                        "parameter-parameter": []
                    }
                }
            },
            "space4": {
                "satisfied-dependencies": "Scalable space for the optional parameter named 'check'.",
                "involved-parameters": [
                    "check"
                ],
                "subspace1": {
                    "parameter": [
                        "check"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": []
                },
                "subspace2": {
                    "parameter": [],
                    "parameter-value": [],
                    "parameter-parameter": []   
                }
            }
        }
    }
}

**Input:**

***INPUT1:***

{
    "/pass": {
        "get": {
            "all-dependencies": [
                "The parameters username and password either exist simultaneously or do not exist at the same time.",
            ]
        }
    }
}

***INPUT2:***

[
    {
        "name": "cookie",
        "param_type": "query",
        "val_type": "string",
        "is_required": true,
        "description": ""
    },
    {
        "name": "username",
        "param_type": "query",
        "val_type": "string",
        "is_required": false,
        "description": ""
    },
    {
        "name": "password",
        "param_type": "query",
        "val_type": "string",
        "is_required": false,
        "description": ""
    }
]

**Output:**

{
    "/pass": {
        "get": {
            "space1": {
                "satisfied-dependencies": "Minimum input space.",
                "involved_parameters": [
                    "cookie"
                ],
                "subspace1": {
                    "parameter": [
                        "cookie"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": []
                }
            },
            "space2": {
                "satisfied-dependencies": "The parameters username and password either exist simultaneously or do not exist at the same time.",
                "involved-parameters": [
                    "username",
                    "password"
                ],
                "subspace1": {
                    "parameter": [],
                    "parameter-value": [],
                    "parameter-parameter": []
                },
                "subspace2": {
                    "parameter": [
                        "username",
                        "password"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": []
                },
                "error_space": {
                    "error_space1": {
                        "parameter": [
                            "username"
                        ],
                        "parameter-value": [],
                        "parameter-parameter": []
                    },
                    "error_space2": {
                        "parameter": [
                            "password"
                        ],
                        "parameter-value": [],
                        "parameter-parameter": []
                    }
                }
            }
        }
    }
}
""".strip()

PROMPT_MULTI_SPACE_PARTITION_final = f"""

# Role

You are an expert in software testing, and your expertise lies in using equivalence class partitioning in black box testing to generate test cases, thereby covering a wider range of user input scenarios.

# Goal

You now need to partition the constraint space of an API based on the constraint relationships between API parameters, so that different constraint spaces can be selected for a subsequent test to generate test cases for different scenarios.

# Instruction

1. Each constraint space (except for the 'minimum input space' and 'expandable parameter spaces') is **uniquely** determined based on the a constraint relationship between parameters.

2. All constraint spaces in an API are labeled as "space1", "space2", "space3",..., "spaceN"(N>=2). Each constraint space contains the following content:
    - involved-parameters: The parameter scope for this constraint space. It explicitly lists all parameters participating in the constraint relationship.
    - subspaceX (X>=1): All cases that satisfy the constraint relationship of the parent space.
    - error_spaceX (X>=0): All cases that violate the constraints of the parent space.

3. Each subspaceX (X>=1) or error_spaceX (X>=0) contains three items:
    - parameter: Existence of parameter. All existing parameters in the case where the subspace satisfies or violates the constraint relationship of the parent space.
    - parameter value: The relationship between parameter and value. Describe the all relationships between parameters and values in natural language when the subspace satisfies or violates the constraints of the parent space.
    - parameter parameter: The relationship between parameters. Describe the all relationships between parameter and parameter in natural language when the subspace satisfies or violates the constraints of the parent space.

4. Regardless of the API, output must include the following two spaces:
    - minimum input space: This space represents the minimum **required** input parameters of the API, with the space name forcibly set to "space1" and only have "subspace1".
    - expandable parameter spaces: Used for dynamically adding optional parameters that have no inter-parameter constraints. You MUST create a distinct, independent space for EACH of these optional parameters. Every such space MUST contain EXACTLY TWO subspaces: A subspace where the optional parameter is present and a subspace where the optional parameter is absent.

# Input Format

{prompt_input_misp}

# Output Format

{prompt_output_misp}

# Examples

{prompt_example_misp}

# Notes

- Ensure that all dependencies are accurately reflected in the partitioned spaces.
- Allow for subspaces that may violate the dependency relationship for comprehensive test coverage.
- Only in the space partitioned based on dependency relationships can there be an erroneous space, that is, there is no erroneous space in the minimum (mandatory) input space and expandable input space.
- It must be noted that the difference in two categories between "parameter-value" and "parameter-parameter" in each message in INPUT1 can be easily confused. You need to confirm whether the left and right sides of the logical symbol are parameters or values.

""".strip()


PARTITION_PROMPT = """

Partition the parameter input space of all methods in all APIs using input space partitioning based on the dependency relationships between parameters.
Follow the specified steps to generate effective and logically consistent test cases.

- **Input Data**: Two JSON inputs, INPUT1 and INPUT2.
  - INPUT1: Contains dependency relationships for parameters in each method of several APIs.
  - INPUT2: Contains specific parameter information for each method of several APIs.

# Space Partition Method Steps

1. **Identify Minimum Input Space**: 
   - For each method in an API, inspect all parameter information in INPUT2.
   - Select the parameters with the minimum input space, which have the following requirements: 1. The required field of the parameters in INPUT2 is true. 2.The natural language description in the description field of the parameter contains the meaning that the parameter must be included in the request, for example: "parameter a must exist", "parameter a must be carried", etc. The parameters that meet the above conditions are used to form the minimum (mandatory) input space, represented as space 1.

2. **Identify Dependency-Based Spaces**:
   - Review all dependencies for each method in INPUT1.
   - Based on these dependencies, select related parameters from INPUT2, denoting these as spaces 2, 3, 4, etc.

3. **Subdivide Spaces**:
   - In each space n (where n != 1), create finer molecular spaces, denoted as n.1, n.2, n.3, etc.
   - Ensure that the subspace includes all cases of dependency constraint relationships represented by the parent space.
   - Allow subspaces that violate dependency relationships, represented as error_Space, to consider all cases of dependency violations in this subspace and list them all.
   - The semantics of this information in each "subspaceX" and "error_spaceX" space are divided into three categories: 1.The existence of parameters. 2.The relationship between parameters and values. 3.The relationship between parameters. Please fill in the category to which each piece of information belongs based on its specific semantics. The categories are as follows: 1."parameter". 2."parameter-value". 3."parameter-parameter".

4. **Add Expandable Parameter Space**:
   - Include a final space containing parameters not identified in the previous steps, i.e., parameters with no dependency relationships and a required field of false, as an expandable parameter input space.

# Output Format

The output should be a valid JSON object structured as follows:

{
    "/path1": {
        "post": {
            "space1": {
                "satisfied-dependencies": "Minimum input space.",
                "involved-parameters": [ Parameter 1, Parameter 2, ... ],
                "subspace1": {
                    "parameter": [
                        "Parameter 1",
                        "Parameter 2",
                        ...
                    ],
                    "parameter-value": [ ... ],
                    "parameter-parameter": [ ... ]
                }
            },
            "space2": {
                "satisfied-dependencies": "Description of dependency 1.",
                "involved-parameters": [ Parameter 3, Parameter 4, Parameter 5, ... ],
                "subspace1": {
                    "parameter": [
                        "Parameter 4"
                    ],
                    "parameter-value": [
                        "Parameter 3 = A"
                    ],
                    "parameter-parameter": [
                        "Parameter 4 = Parameter 5"
                    ]
                },
                "subspace2": {
                    "parameter": [ ... ],
                    "parameter-value": [
                        "Parameter 3 != A"
                    ],
                    "parameter-parameter": [...]
                }
                ...
                "error_space": {/* The all list of ERROR space because it violated the dependency relationship */
                    "error_space1": {
                        "parameter": [
                            "Parameter 4"
                        ],
                        "parameter-value": [
                            "Parameter 3 != A"
                        ],
                        "parameter-parameter": []
                    },
                    "error_space2": {
                        ...
                    },
                    ...
                }
            },
            ...
        }
    },
    "/path2": {
        "get": {
            "space1": {
                "satisfied-dependencies": "Minimum input space.",
                "involved-parameters": [ ... ],
                "subspace1": {
                    ...
                }
            },
            ...
        }
    }
}

# Examples

**Input:**

***INPUT1:***

{
    "/hello": {
        "post": {
            "all-dependencies": [
                "Either the parameter male or the parameter female is required.",
                "The parameter rule is only available when the parameter sex is set to auto."
            ]
        }
    }
}

***INPUT2:***

{
    "/hello": {
        "post": {
            "parameters": [],
            "requestBody": [
                {
                    "name": "male",
                    "type": "string",
                    "description": "The male to be checked. This or 'female' is required.",
                    "required": false
                },
                {
                    "name": "female",
                    "type": "string",
                    "description": "",
                    "required": false
                },
                {
                    "name": "sex",
                    "type": "string",
                    "description": "",
                    "required": true
                },
                {
                    "name": "rule",
                    "type": "string",
                    "description": "If rule is exist, the parameter sex is set to auto.",
                    "required": false
                },
                {
                    "name": "check",
                    "type": "string",
                    "description": "",
                    "required": false
                }
            ],
            "x-dependencies": []
        }
    }
}

**Output:**

{
    "/hello": {
        "post": {
            "space1": {
                "satisfied-dependencies": "Minimum input space.",
                "involved-parameters": [
                    "sex"
                ],
                "subspace1": {
                    "parameter": [
                        "sex"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": []
                }
            },
            "space2": {
                "satisfied-dependencies": "Either the parameter male or the parameter female is required.",
                "involved-parameters": [
                    "male",
                    "female"
                ],
                "subspace1": {
                    "parameter": [
                        "male"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": []
                },
                "subspace2": {
                    "parameter": [
                        "female"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": []
                },
                "error_space": {
                    "error_space1": {
                        "parameter": [
                            "male",
                            "female"
                        ],
                        "parameter-value": [],
                        "parameter-parameter": []
                    }
                }
            },
            "space3": {
                "satisfied-dependencies": "The parameter rule is only available when the parameter sex is set to auto.",
                "involved-parameters": [
                    "rule",
                    "sex"
                ],
                "subspace1": {
                    "parameter": [
                        "rule"
                    ],
                    "parameter-value": [
                        "sex = auto"
                    ],
                    "parameter-parameter": []
                },
                "error_space": {
                    "error_space1": {
                        "parameter": [
                            "rule"
                        ],
                        "parameter-value": [
                            "sex != auto"
                        ],
                        "parameter-parameter": []
                    }
                }
            },
            "space4": {
                "satisfied-dependencies": "Scalable space.",
                "involved-parameters": [
                    "check"
                ],
                "subspace1": {
                    "parameter": [
                        "check"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": []
                },
                {
                    "parameter": [],
                    "parameter-value": [],
                    "parameter-parameter": []
                }
            }
        }
    }
}

**Input:**

***INPUT1:***

{
    "/pass": {
        "get": {
            "all-dependencies": [
                "The parameters username and password either exist simultaneously or do not exist at the same time.",
            ]
        }
    }
}

***INPUT2:***

{
    "/pass": {
        "get": {
            "parameters": [
                {
                    "name": "cookie",
                    "type": "string",
                    "description": "",
                    "required": true
                },
                {
                    "name": "username",
                    "type": "string",
                    "description": "",
                    "required": false
                },
                {
                    "name": "password",
                    "type": "string",
                    "description": "",
                    "required": false
                }
            ],
            "requestBody": [],
            "x-dependencies": [
                "AllOrNone(username, password);"
            ]
        }
    }
}

**Output:**

{
    "/pass": {
        "get": {
            "space1": {
                "satisfied-dependencies": "Minimum input space.",
                "involved-parameters": [
                    "cookie"
                ],
                "subspace1": {
                    "parameter": [
                        "cookie"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": []
                }
            },
            "space2": {
                "satisfied-dependencies": "The parameters username and password either exist simultaneously or do not exist at the same time.",
                "involved-parameters": [
                    "username",
                    "password"
                ],
                "subspace1": {
                    "parameter": [],
                    "parameter-value": [],
                    "parameter-parameter": []
                },
                "subspace2": {
                    "parameter": [
                        "username",
                        "password"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": []
                },
                "error_space": {
                    "error_space1": {
                        "parameter": [
                            "username"
                        ],
                        "parameter-value": [],
                        "parameter-parameter": []
                    },
                    "error_space2": {
                        "parameter": [
                            "password"
                        ],
                        "parameter-value": [],
                        "parameter-parameter": []
                    }
                }
            }
        }
    }
}

# Notes

- Ensure that all dependencies are accurately reflected in the partitioned spaces.
- Allow for subspaces that may violate the dependency relationship for comprehensive test coverage.
- Only in the space partitioned based on dependency relationships can there be an erroneous space, that is, there is no erroneous space in the minimum (mandatory) input space and expandable input space.
- It must be noted that the difference in two categories between "parameter-value" and "parameter-parameter" in each message can be easily confused. You need to confirm whether the left and right sides of the logical symbol are parameters or values.

""".strip()
