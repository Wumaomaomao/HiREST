
# Role
# 你是一位精通软件测试的专家，你最擅长使用黑盒测试中的等价类划分来生成测试用例，从而覆盖更广的用户输入情况。
# Goal
# 混合提供的多参数约束空间和每个参数的具体valid值空间，最终生成一个“融合后的约束值空间”，以便生成后续的测试用例。
# Instruction
# 1.你需要为“subspaceX”和“error_spaceX”中所有必需的参数筛选其符合约束空间要求的参数值空间，你必须遵循以下几个方面来实现更好的匹配：
#     - 所有参数。你需要先找出约束空间中涉及的所有参数，包含存在和被排斥存在性的参数。
#     - 约束信息。约束空间中包含满足或违反父空间的约束条件，这些约束条件在“parameter”，“parameter-value”，“parameter-parameter”中显式的提供，你需要根据约束条件来筛选符合约束条件的参数值空间。若无约束条件，那么选择所有的valid参数值空间。
#     - 排斥存在性的参数。对于约束空间中被排斥存在性的参数，你需要包含一个特殊的单参数值空间名为<MISS_KEY>。
# 2.提取参数值空间时，需要携带该值空间满足的正则表达式。如果空间中示例值包含多个值类型，那么不需要携带格式，直接设置为null。
# Input Format
#
# INPUT1提供了API的多参数约束空间，spaceX是由每条约束确定的父空间，其中会有若干个subspaceX（满足父空间约束）和error_spaceX(违反父空间约束)子空间。
# 每个子空间中又包含“parameter”，“parameter-value”，“parameter-parameter”三个字段的约束信息，分别表示当前子空间参数存在性，参数与值之间的关系，参数与参数之间的关系。
# such as
#
# INPUT2提供了该API下包含所有参数值空间的列表，参数信息包含参数名称，参数类型，参数必要性，参数格式，有效参数值空间。
# such as
# Notes
# - 如果在某个subspaceX或error_spaceX中没有任何参数，且体现了约束对参数键的排斥关系，那么你需要在融合后的空间中为该参数附上一个特殊的单参数值空间，命名为<MISS_KEY>，表示该参数在该空间中被排斥存在。

prompt_input_mix = r"""
INPUT1 provides a multi parameter constraint space for the API, where "spaceX" is a parent space determined by each constraint, and there are several "subspaceX" (satisfying the parent space constraint) and "error_spaceX" (violating the parent space constraint) subspaces.
Each subspace contains constraint information for three fields: "parameter", "parameter-value", and "parameter-parameter", which respectively represent the existence of parameters in the current subspace, the relationship between parameters and values, and the relationship between parameters.
Such as:

{
    "/v1/register": {
        "post": {
            "space1": {
                "satisfied-dependencies": "Minimum input space.",
                "involved-parameters": [
                    "username",
                    "password"
                ],
                "subspace1": {
                    "parameter": [
                        "username",
                        "password"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": []
                }
            },
            "space2": {
                "satisfied-dependencies": "...",
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
                },
                "error_space": {
                    "error_space1": {
                        "parameter": [ ... ],
                        "parameter-value": [ ... ],
                        "parameter-parameter": [ ... ]
                    }
                }
            },
            "space3": {
                "satisfied-dependencies": "...",
                "involved-parameters": [ ... ],
                "subspace1": { ... },
                "error_space": {
                    "error_space1": { ... }
                }
            }
        }
    }
}

INPUT2 provides a list of all parameter value spaces under this API, including parameter name, parameter type, parameter necessity, parameter format, valid parameter value space.
Such as:

[
    {
        "parameter_name": "A",
        "type": "string",
        "required": true,
        "format": [
            "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,12}$"
        ],
        "valid_input_space_categories": [
            {
                "input_space_category": "Lowercase English letters and numbers",
                "description": "The parameter username only contains lowercase English letters and numbers.",
                "representative_samples": [
                    "ui12934kj1",
                    "12o310pazdc",
                    "abcdefghijk1"
                ]
            },
            {
                "input_space_category": "Uppercase English letters and numbers",
                "description": "The parameter username contains only uppercase English letters and numbers.",
                "representative_samples": [
                    "OSAGFJK123",
                    "129011KAF"
                ]
            },
            {
                "input_space_category": "Uppercase and lowercase English letters and numbers",
                "description": "The parameter username contains only uppercase English letters, lowercase English letters and numbers.",
                "representative_samples": [
                    "afK8HJas11",
                    "918Knnna1II"
                ]
            },
            {
                "input_space_category": "Administrator account",
                "description": "The value of parameter username is the administrator account.",
                "representative_samples": [
                    "admin"
                ]
            }
        ],
        "operationId": null,
        "url_path": "/v1/register",
        "http_verb": "post"
    },
    ...
]
""".strip()
prompt_output_mix = """
You need to output in JSON format as follows：

{
    "/examples": {
        "get": {
            "space1": {
                "satisfied-dependencies": "Minimum input space.",
                "involved-parameters": [
                    "username",
                    "password"
                ],
                "subspace1": {
                    "single-parameter-spaces": {
                        "password": [
                            {
                                "tag": "valid",
                                "type": "string",
                                "format": "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,12}$",
                                "input_space_category": "Lowercase English letters and numbers",
                                "description": "The parameter username only contains lowercase English letters and numbers.",
                                "representative_samples": [
                                    "kao123k51j",
                                    "appl23623"
                                ]
                            },
                            {
                                "tag": "valid",
                                "type": "string",
                                "format": "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,12}$",
                                "input_space_category": "Uppercase English letters and numbers",
                                "description": "The parameter username contains only uppercase English letters and numbers.",
                                "representative_samples": [
                                    "KKKOAF123"
                                ]
                            },
                            ...
                        ],
                        "question": [
                            {
                                ...
                            },
                            ...
                        ],
                        "A": [ ... ],
                        "B": [ ... ],
                        ...
                    },
                    "parameter": [
                        "password",
                        "question",
                        "A",
                        "B"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": [
                        "A = B",
                        ...
                    ]
                }
            },
            "space2": {
                "satisfied-dependencies": "Either the parameter info or data must be provided.",
                "involved-parameters": [
                    "info",
                    "data"
                ],
                "subspace1": {
                    "single-parameter-spaces": {
                        ...
                    },
                    "parameter": [
                        "info"
                    ],
                    "parameter-value": [ ... ],
                    "parameter-parameter": [ ... ]
                },
                "subspace2": {
                    "single-parameter-spaces": {
                        ...
                    },
                    "parameter": [
                        "data"
                    ],
                    "parameter-value": [ ... ],
                    "parameter-parameter": [ ... ]
                },
                "error_space": {
                    "error_space1": {
                        "single-parameter-spaces": {
                            ...
                        },
                        "parameter": [ ... ],
                        "parameter-value": [ ... ],
                        "parameter-parameter": [ ... ]
                    }
                }
            }
        }
    }
}
""".strip()
prompt_example_mix = r"""
**Input:**

***INPUT1:***

{
    "/v1/register": {
        "post": {
            "space1": {
                "satisfied-dependencies": "Minimum input space.",
                "involved-parameters": [
                    "username",
                    "password"
                ],
                "subspace1": {
                    "parameter": [
                        "username",
                        "password"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": []
                }
            },
            "space2": {
                "satisfied-dependencies": "Either the parameter email or phoneNumber must be provided.",
                "involved-parameters": [
                    "email",
                    "phoneNumber"
                ],
                "subspace1": {
                    "parameter": [
                        "email"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": []
                },
                "subspace2": {
                    "parameter": [
                        "phoneNumber"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": []
                },
                "error_space": {
                    "error_space1": {
                        "parameter": [
                            "email",
                            "phoneNumber"
                        ],
                        "parameter-value": [],
                        "parameter-parameter": []
                    },
                    "error_space2": {
                        "parameter": [],
                        "parameter-value": [],
                        "parameter-parameter": []
                    }
                }
            },
            "space3": {
                "satisfied-dependencies": "The parameter confirmPassword must be equal to parameter password.",
                "involved-parameters": [
                    "confirmPassword",
                    "password"
                ],
                "subspace1": {
                    "parameter": [
                        "confirmPassword"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": [
                        "confirmPassword = password"
                    ]
                },
                "error_space": {
                    "error_space1": {
                        "parameter": [
                            "confirmPassword"
                        ],
                        "parameter-value": [],
                        "parameter-parameter": [
                            "confirmPassword != password"
                        ]
                    }
                }
            },
            "space4": {
                "satisfied-dependencies": "If the value of parameter username is admin, the value of parameter password must be equal to 111",
                "involved-parameters": [
                    "username",
                    "password"
                ],
                "subspace1": {
                    "parameter": [],
                    "parameter-value": [
                        "username = admin",
                        "password = 111"
                    ],
                    "parameter-parameter": []
                },
                "error_space": {
                    "error_space1": {
                        "parameter": [],
                        "parameter-value": [
                            "username = admin",
                            "password != 111"
                        ],
                        "parameter-parameter": []
                    }
                }
            },
            "space5": {
                "satisfied-dependencies": "Scalable space.",
                "involved-parameters": [
                    "userInfo"
                ],
                "subspace1": {
                    "parameter": [
                        "userInfo"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": []
                }
            }
        }
    }
}

***INPUT2:***

[
    {
        "parameter_name": "username",
        "type": "string",
        "required": true,
        "format": [
            "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,12}$",
            "^admin$"
        ],
        "valid_input_space_categories": [
            {
                "input_space_category": "Lowercase English letters and numbers",
                "description": "The parameter username only contains lowercase English letters and numbers.",
                "representative_samples": [
                    "ui12934kj1",
                    "12o310pazdc",
                    "abcdefghijk1"
                ]
            },
            {
                "input_space_category": "Uppercase English letters and numbers",
                "description": "The parameter username contains only uppercase English letters and numbers.",
                "representative_samples": [
                    "OSAGFJK123",
                    "129011KAF"
                ]
            },
            {
                "input_space_category": "Uppercase and lowercase English letters and numbers",
                "description": "The parameter username contains only uppercase English letters, lowercase English letters and numbers.",
                "representative_samples": [
                    "afK8HJas11",
                    "918Knnna1II"
                ]
            },
            {
                "input_space_category": "Administrator account",
                "description": "The value of parameter username is the administrator account.",
                "representative_samples": [
                    "admin"
                ]
            }
        ],
        "operationId": null,
        "url_path": "/v1/register",
        "http_verb": "post"
    },
    {
        "parameter_name": "password",
        "type": "string",
        "required": true,
        "format": [
            "^\\d{6}$",
            "^111$"
        ],
        "valid_input_space_categories": [
            {
                "input_space_category": "6-digit numerical string",
                "description": "6-digit numerical string.",
                "representative_samples": [
                    "123456",
                    "665324"
                ]
            },
            {
                "input_space_category": "Administrator password",
                "description": "The value of parameter password is the administrator password.",
                "representative_samples": [
                    "111"
                ]
            }
        ],
        "operationId": null,
        "url_path": "/v1/register",
        "http_verb": "post"
    },
    {
        "parameter_name": "email",
        "type": "string",
        "required": false,
        "format": [
            "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
        ],
        "valid_input_space_categories": [
            {
                "input_space_category": "valid email format",
                "description": "The parameter email contains correct email formats.",
                "representative_samples": [
                    "user@example.com",
                    "hello.world@domain.co.uk"
                ]
            },
            {
                "input_space_category": "<MISS_KEY>",
                "description": "The parameter email is missing from the request.",
                "representative_samples": [
                    null
                ]
            }
        ],
        "operationId": null,
        "url_path": "/v1/register",
        "http_verb": "post"
    },
    {
        "parameter_name": "phoneNumber",
        "type": "string",
        "required": false,
        "format": [
            "^1[3-9]\\{9}$"
        ],
        "valid_input_space_categories": [
            {
                "input_space_category": "valid phoneNumber format",
                "description": "The parameter phoneNumber contains correct phone number formats.",
                "representative_samples": [
                    "13812345678",
                    "19987654321"
                ]
            },
            {
                "input_space_category": "<MISS_KEY>",
                "description": "The parameter phoneNumber is missing from the request.",
                "representative_samples": [
                    null
                ]
            }
        ],
        "operationId": null,
        "url_path": "/v1/register",
        "http_verb": "post"
    },
    {
        "parameter_name": "confirmPassword",
        "type": "string",
        "required": false,
        "format": [
            "^\\d{6}$"
        ],
        "valid_input_space_categories": [
            {
                "input_space_category": "6-digit numerical string",
                "description": "6-digit numerical string.",
                "representative_samples": [
                    "930256",
                    "561134"
                ]
            },
            {
                "input_space_category": "<MISS_KEY>",
                "description": "The parameter confirmPassword is missing from the request.",
                "representative_samples": [
                    null
                ]
            }
        ],
        "operationId": null,
        "url_path": "/v1/register",
        "http_verb": "post"
    },
    {
        "parameter_name": "userInfo",
        "type": "string",
        "required": false,
        "format": [
            "^[\\s\\S]*$"
        ],
        "valid_input_space_categories": [
            {
                "input_space_category": "Short Text",
                "description": "A short text input for quick grammar checks.",
                "representative_samples": [
                    "Hello world!",
                    "This is an user information."
                ]
            },
            {
                "input_space_category": "Long Text",
                "description": "A longer text input for comprehensive grammar checks.",
                "representative_samples": [
                    "Once upon a time, in a land far, far away, there lived a king who ruled with wisdom and kindness.",
                    "In the midst of the bustling city, there was a small, quaint café that served the best coffee in town."
                ]
            },
            {
                "input_space_category": "<MISS_KEY>",
                "description": "The parameter userInfo is missing from the request.",
                "representative_samples": [
                    null
                ]
            }
        ],
        "operationId": null,
        "url_path": "/v1/register",
        "http_verb": "post"
    },
    {
        "parameter_name": "username",
        "type": "string",
        "required": true,
        "format": [
            "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,12}$"
        ],
        "valid_input_space_categories": [
            {
                "input_space_category": "Lowercase English letters and numbers",
                "description": "The parameter username only contains lowercase English letters and numbers.",
                "representative_samples": [
                    "1111aaaa"
                ]
            },
            {
                "input_space_category": "Uppercase English letters and numbers",
                "description": "The parameter username contains only uppercase English letters and numbers.",
                "representative_samples": [
                    "1111AAAA"
                ]
            },
            {
                "input_space_category": "Uppercase and lowercase English letters and numbers",
                "description": "The parameter username contains only uppercase English letters, lowercase English letters and numbers.",
                "representative_samples": [
                    "1111aaAA"
                ]
            }
        ],
        "operationId": null,
        "url_path": "/v1/settingInformation",
        "http_verb": "get"
    }
]

**Output:**

{
    "/v1/register": {
        "post": {
            "space1": {
                "satisfied-dependencies": "Minimum input space.",
                "involved-parameters": [
                    "username",
                    "password"
                ],
                "subspace1": {
                    "single-parameter-spaces": {
                        "username": [
                            {
                                "tag": "valid",
                                "type": "string",
                                "format": "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,12}$",
                                "input_space_category": "Lowercase English letters and numbers",
                                "description": "The parameter username only contains lowercase English letters and numbers.",
                                "representative_samples": [
                                    "ui12934kj1",
                                    "12o310pazdc",
                                    "abcdefghijk1"
                                ]
                            },
                            {
                                "tag": "valid",
                                "type": "string",
                                "format": "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,12}$",
                                "input_space_category": "Uppercase English letters and numbers",
                                "description": "The parameter username contains only uppercase English letters and numbers.",
                                "representative_samples": [
                                    "OSAGFJK123",
                                    "129011KAF"
                                ]
                            },
                            {
                                "tag": "valid",
                                "type": "string",
                                "format": "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,12}$",
                                "input_space_category": "Uppercase and lowercase English letters and numbers",
                                "description": "The parameter username contains only uppercase English letters, lowercase English letters and numbers.",
                                "representative_samples": [
                                    "afK8HJas11",
                                    "918Knnna1II"
                                ]
                            },
                            {
                                "tag": "valid",
                                "type": "string",
                                "format": "^admin$",
                                "input_space_category": "Administrator account",
                                "description": "The value of parameter username is the administrator account.",
                                "representative_samples": [
                                    "admin"
                                ]
                            }
                        ],
                        "password": [
                            {
                                "tag": "valid",
                                "type": "string",
                                "format": "^\\d{6}$",
                                "input_space_category": "6-digit numerical string",
                                "description": "6-digit numerical string.",
                                "representative_samples": [
                                    "123456",
                                    "665324"
                                ]
                            },
                            {
                                "tag": "valid",
                                "type": "string",
                                "format": "^111$",
                                "input_space_category": "Administrator password",
                                "description": "The value of parameter password is the administrator password.",
                                "representative_samples": [
                                    "111"
                                ]
                            },
                        ]
                    },
                    "parameter": [
                        "username",
                        "password"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": []
                }
            },
            "space2": {
                "satisfied-dependencies": "Either the parameter email or phoneNumber must be provided.",    
                "involved-parameters": [
                    "email",
                    "phoneNumber"
                ],
                "subspace1": {
                    "single-parameter-spaces": {
                        "email": [
                            {
                                "tag": "valid",
                                "type": "string",
                                "format": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                                "input_space_category": "valid email format",
                                "description": "The parameter email contains correct email formats.",
                                "representative_samples": [
                                    "user@example.com",
                                    "hello.world@domain.co.uk"
                                ]
                            }
                        ],
                        "phoneNumber": [
                        {
                            "tag": "valid",
                            "type": null,
                            "format": null,
                            "input_space_category": "<MISS_KEY>",
                            "description": "The parameter phoneNumber is missing from the request.",
                            "representative_samples": [
                                null
                            ]
                        }]
                    },
                    "parameter": [
                        "email"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": []
                },
                "subspace2": {
                    "single-parameter-spaces": {
                        "email" : [{
                            "tag": "valid",
                            "type": null,
                            "format": null,
                            "input_space_category": "<MISS_KEY>",
                            "description": "The parameter email is missing from the request.",
                            "representative_samples": [
                                null
                            ]
                        }],
                        "phoneNumber": [
                            {
                                "tag": "valid",
                                "type": "string",
                                "format": "^1[3-9]\\{9}$",
                                "input_space_category": "valid phoneNumber format",
                                "description": "The parameter phoneNumber contains correct phone number formats.",
                                "representative_samples": [
                                    "13812345678",
                                    "19987654321"
                                ]
                            }
                        ]
                    },
                    "parameter": [
                        "phoneNumber"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": []
                },
                "error_space": {
                    "error_space1": {
                        "single-parameter-spaces": {
                            "email": [
                                {
                                    "tag": "valid",
                                    "type": "string",
                                    "format": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                                    "input_space_category": "valid email format",
                                    "description": "The parameter email contains correct email formats.",
                                    "representative_samples": [
                                        "user@example.com",
                                        "hello.world@domain.co.uk"
                                    ]
                                }
                            ],
                            "phoneNumber": [
                            {
                                "tag": "valid",
                                "type": "string",
                                "format": "^1[3-9]\\{9}$",
                                "input_space_category": "valid phoneNumber format",
                                "description": "The parameter phoneNumber contains correct phone number formats.",
                                "representative_samples": [
                                    "13812345678",
                                    "19987654321"
                                ]
                            }
                        ]
                        },
                        "parameter": [
                            "email",
                            "phoneNumber"
                        ],
                        "parameter-value": [],
                        "parameter-parameter": []
                    },
                    "error_space2": {
                        "single-parameter-spaces": {
                            "email": [
                                {
                                    "tag": "valid",
                                    "type": null,
                                    "format": null,
                                    "input_space_category": "<MISS_KEY>",
                                    "description": "The parameter email is missing from the request.",
                                    "representative_samples": [
                                        null
                                    ]
                                }
                            ],
                            "phoneNumber": [
                                {
                                    "tag": "valid",
                                    "type": null,
                                    "format": null,
                                    "input_space_category": "<MISS_KEY>",
                                    "description": "The parameter phoneNumber is missing from the request.",
                                    "representative_samples": [
                                        null
                                    ]
                                }
                            ]
                        },
                        "parameter": [],
                        "parameter-value": [],
                        "parameter-parameter": []
                    }
            },
            "space3": {
                "satisfied-dependencies": "The parameter confirmPassword must be equal to parameter password.",     
                "involved-parameters": [
                    "confirmPassword",
                    "password"
                ],
                "subspace1": {
                    "single-parameter-spaces": {
                        "confirmPassword": [
                            {
                                "tag": "valid",
                                "type": "string",
                                "format": "^\\d{6}$",
                                "input_space_category": "6-digit numerical string",
                                "description": "6-digit numerical string.",
                                "representative_samples": [
                                    "930256",
                                    "561134"
                                ]
                            }
                        ],
                        "password": [
                            {
                                "tag": "valid",
                                "type": "string",
                                "format": "^\\d{6}$",
                                "input_space_category": "6-digit numerical string",
                                "description": "6-digit numerical string.",
                                "representative_samples": [
                                    "123456",
                                    "665324"
                                ]
                            },
                            {
                                "tag": "valid",
                                "type": "string",
                                "format": "^111$",
                                "input_space_category": "Administrator password",
                                "description": "The value of parameter password is the administrator password.",
                                "representative_samples": [
                                    "111"
                                ]
                            },
                        ]
                    },
                    "parameter": [
                        "confirmPassword"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": [
                        "confirmPassword = password"
                    ]
                },
                "error_space": {
                    "error_space1": {
                        "single-parameter-spaces": {
                            "confirmPassword": [
                                {
                                    "tag": "valid",
                                    "type": "string",
                                    "format": "^\\d{6}$",
                                    "input_space_category": "6-digit numerical string",
                                    "description": "6-digit numerical string.",
                                    "representative_samples": [
                                        "930256",
                                        "561134"
                                    ]
                                }
                            ],
                            "password": [
                                {
                                    "tag": "valid",
                                    "type": "string",
                                    "format": "^\\d{6}$",
                                    "input_space_category": "6-digit numerical string",
                                    "description": "6-digit numerical string.",
                                    "representative_samples": [
                                        "123456",
                                        "665324"
                                    ]
                                },
                                {
                                    "tag": "valid",
                                    "type": "string",
                                    "format": "^111$",
                                    "input_space_category": "Administrator password",
                                    "description": "The value of parameter password is the administrator password.",
                                    "representative_samples": [
                                        "111"
                                    ]
                                }
                            ]
                        },
                        "parameter": [
                            "confirmPassword"
                        ],
                        "parameter-value": [],
                        "parameter-parameter": [
                            "confirmPassword != password"
                        ]
                    }
                }
            },
            "space4": {
                "satisfied-dependencies": "If the value of parameter username is admin, the value of parameter password must be equal to 111",
                "involved-parameters": [
                    "username",
                    "password"
                ],
                "subspace1": {
                    "single-parameter-spaces": {
                        "username": [
                            {
                                "tag": "valid",
                                "type": "string",
                                "format": "^admin$",
                                "input_space_category": "Administrator account",
                                "description": "The value of parameter username is the administrator account.",
                                "representative_samples": [
                                    "admin"
                                ]
                            }
                        ],
                        "password": [
                            {
                                "tag": "valid",
                                "type": "string",
                                "format": "^111$",
                                "input_space_category": "Administrator password",
                                "description": "The value of parameter password is the administrator password.",
                                "representative_samples": [
                                    "111"
                                ]
                            }
                        ]
                    },
                    "parameter": [],
                    "parameter-value": [
                        "username = admin",
                        "password = 111"
                    ],
                    "parameter-parameter": []
                },
                "error_space": {
                    "error_space1": {
                        "single-parameter-spaces": {
                            "username": [
                                {
                                    "tag": "valid",
                                    "type": "string",
                                    "format": "^admin$",
                                    "input_space_category": "Administrator account",
                                    "description": "The value of parameter username is the administrator account.",
                                    "representative_samples": [
                                        "admin"
                                    ]
                                }
                            ],
                            "password": [
                                {
                                    "tag": "valid",
                                    "type": "string",
                                    "format": "^\\d{6}$",
                                    "input_space_category": "6-digit numerical string",
                                    "description": "6-digit numerical string.",
                                    "representative_samples": [
                                        "123456",
                                        "665324"
                                    ]
                                }
                            ]
                        },
                        "parameter": [],
                        "parameter-value": [
                            "username = admin",
                            "password != 111"
                        ],
                        "parameter-parameter": []
                    }
                }
            },
            "space5": {
                "satisfied-dependencies": "Scalable space.",
                "involved-parameters": [
                    "userInfo"
                 ],
                "subspace1": {
                    "single-parameter-spaces": {
                        "userInfo": [
                            {
                                "tag": "valid",
                                "type": "string",
                                "format": "^[\\s\\S]*$",
                                "input_space_category": "Short Text",
                                "description": "A short text input for quick grammar checks.",
                                "representative_samples": [
                                    "Hello world!",
                                    "This is an user information."
                                ]
                            },
                            {
                                "tag": "valid",
                                "type": "string",
                                "format": "^[\\s\\S]*$",
                                "input_space_category": "Long Text",
                                "description": "A longer text input for comprehensive grammar checks.",
                                "representative_samples": [
                                    "Once upon a time, in a land far, far away, there lived a king who ruled with wisdom and kindness.",
                                    "In the midst of the bustling city, there was a small, quaint café that served the best coffee in town."
                                ]
                            }
                        ]
                    },
                    "parameter": [
                        "userInfo"
                    ],
                    "parameter-value": [],
                    "parameter-parameter": []
                }
            }
        }
    }
}
""".strip()

PROMPT_MIXED_SPACE_PARTITION_final = f"""

# Role

You are an expert in software testing, and your expertise lies in using equivalence class partitioning in black box testing to generate test cases, thereby covering a wider range of user input scenarios.

# Goal

Mix the multi parameter constraint space provided with the specific valid value spaces of each parameter, and finally generate a "fused constraint value space" for generating subsequent test cases.

# Instruction

1. You need to filter the parameter value space that meets the constraint space requirements for all necessary parameters in "subspaceX" and "error_spaceX". You must follow the following aspects to achieve better matching:
    - All parameters. You need to first identify all parameters involved in the constraint space (both explicitly present and explicitly absent/excluded) to ensure there are no omissions.
    - Constraints information. The constraint space contains constraints that satisfy or violate the parent space, which are explicitly provided in "parameter", "parameter-value", and "parameter-parameter". You need to filter the parameter value space that meets the constraint conditions based on the constraints. If there are no constraints, then select all parameter value spaces.
    - Absent Parameters: For any parameter whose existence is excluded in the constraint space, you MUST assign it a special single-value space named <MISS_KEY>.

2. When extracting the parameter value space, it is necessary to carry the regular expression that the value space satisfies. If the example values in the value space contain multiple value types, there is no need to carry the format, just set it to null.

# Input Format

{prompt_input_mix}

# Output Format

{prompt_output_mix}

# Examples

{prompt_example_mix}

# Notes

- If a parameter is excluded from a subspaceX or error_spaceX due to constraints, you MUST assign it a special single-value space named <MISS_KEY> in the fused output to represent its required absence.

""".strip()
part1  = ""
# part1 = r"""

# You now have a task: to fill some single parameter spaces with smaller granularity in multi parameter subspaces determined by constraint relationships.

# This task has two JSON format input data files INPUT1 and INPUT2, with specific information as follows:

# About INPUT1:
# 1.Starting from the path of the REST API, followed by the method name, there are several spaces named "spaceX" under the method name, such as space1, space2. These spaces are determined by multi parameter dependencies and constraints under this method, which are explained in natural language in the "satisfied-dependencies" field under the "spaceX".
# 2.In each space, there are several subspaces named "subspaceX" and one subspace named "error_space", which in turn have several error subspaces named "error_spaceX". These subspaces are divided into valid and invalid spaces based on dependency constraint information, and contain information about parameters.
# 3.In each valid and invalid subspace, the information of parameters is divided into three categories: 1. Existence of parameters, represented by "parameter".(It should be noted that the parameter existence here means that the parameter only needs to exist and does not need to satisfy the latter two relationships. If the parameter is listed in the latter two relationships and is not listed here, it is also assumed that the parameter should exist.) 2. The relationship between parameters and values is represented by "parameter-value". 3. The relationship between parameters is represented by "parameter-parameter".

# About INPUT2:
# 1.This is a list that contains information about several parameters.
# 2.The information field of the parameter contains the parameter name: "parameter_name", the parameter type: "type", the parameter necessity: "required", the parameter format: "format", the valid parameter space type: "valid_input_space_categories", the invalid parameter space type: "invalid_input_space_categories", the API operation ID: "operationId", the path: "url_path" and the method: "http_verb".
# 3.The "valid_input_space_categories" and "invalid_input_space_categories" contain two lists, each containing several different single parameter value spaces. Each space has three fields: "input_space_category", "description", and "representative_samples", which respectively represent the spatial type, specific description of spatial information, and spatial value examples.

# Task description:

# You need to match the appropriate single parameter space in INPUT2 for each subspace in INPUT1, including "subspaceX" and "error_spaceX".
# Firstly, in INPUT1, traverse all "subspaceX" and "error_spaceX" subspaces under each method, find all the required parameters in these spaces (please note that the required parameters referred to here are not just parameters in "parameter", but all parameters involved in the three types of "parameter", "parameter-value" and "parameter-parameter"!), and match all the single parameter spaces of this parameter in INPUT2, whether they are valid or invalid. At this point, it is necessary to ensure that the parameters searched in INPUT2 are consistent with the spatial paths and methods in INPUT1.
# Secondly, you need to consider the "parameter-value" field in "subspaceX" and "error_spaceX", and based on the constraint relationship between parameters and values, exclude spaces that do not meet the constraint conditions from all single parameter spaces corresponding to the parameters identified in the previous step. For example, if there is a message "a<100" from "parameter-value" field in the subspaceX of INPUT1, then you only need to leave all single parameter spaces under the corresponding field of INPUT2 that satisfy a<100, and remove all subspaces with a>=100.
# Thirdly, when extracting a single parameter space from INPUT2, it is necessary to carry the regular expression that the space satisfies. Specifically, select the format from the list of "format" fields in the parameter information of INPUT2. For selecting invalid spaces, there is no need to carry a format.
# Fourthly, based on the example values of the "representative_samples" field in the single parameter space, reset the type of parameters in each single parameter space. If the example value contains more than one type, such as an illegal space containing boolean, int, string, then the type is directly filled with "null".
# Finally, keep the relationship between parameters in each INPUT1 subspace unchanged.
# """

part2 = ""
# part2 = """
# # Output format

# You need to output in JSON format as follows：

# {
#     "/examples": {
#         "get": {
#             "space1": {
#                 "satisfied-dependencies": "Minimum input space.",
#                 "subspace1": {
#                     "single-parameter-spaces": {
#                         "password": [
#                             {
#                                 "tag": "valid",
#                                 "type": "string",
#                                 "format": "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,12}$",
#                                 "input_space_category": "Lowercase English letters and numbers",
#                                 "description": "The parameter username only contains lowercase English letters and numbers.",
#                                 "representative_samples": [
#                                     "kao123k51j",
#                                     "appl23623"
#                                 ]
#                             },
#                             {
#                                 "tag": "valid",
#                                 "type": "string",
#                                 "format": "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,12}$",
#                                 "input_space_category": "Uppercase English letters and numbers",
#                                 "description": "The parameter username contains only uppercase English letters and numbers.",
#                                 "representative_samples": [
#                                     "KKKOAF123"
#                                 ]
#                             },
#                             {
#                                 "tag": "invalid",
#                                 "type": "string",
#                                 "format": null,
#                                 "input_space_category": "Pure digital",
#                                 "description": "Only contains numbers.",
#                                 "representative_samples": [
#                                     "3245565733"
#                                 ]
#                             },
#                             {
#                                 "tag": "invalid",
#                                 "type": null,
#                                 ...
#                             },
#                             ...
#                         ],
#                         "question": [
#                             {
#                                 ...
#                             },
#                             ...
#                         ],
#                         "A": [ ... ],
#                         "B": [ ... ],
#                         ...
#                     },
#                     "parameter": [
#                         "password",
#                         "question",
#                         "A",
#                         "B"
#                     ],
#                     "parameter-value": [],
#                     "parameter-parameter": [
#                         "A = B",
#                         ...
#                     ]
#                 }
#             },
#             "space2": {
#                 "satisfied-dependencies": "Either the parameter info or data must be provided.",
#                 "subspace1": {
#                     "single-parameter-spaces": {
#                         ...
#                     },
#                     "parameter": [
#                         "info"
#                     ],
#                     "parameter-value": [ ... ],
#                     "parameter-parameter": [ ... ]
#                 },
#                 "subspace2": {
#                     "single-parameter-spaces": {
#                         ...
#                     },
#                     "parameter": [
#                         "data"
#                     ],
#                     "parameter-value": [ ... ],
#                     "parameter-parameter": [ ... ]
#                 },
#                 "error_space": {
#                     "error_space1": {
#                         "single-parameter-spaces": {
#                             ...
#                         },
#                         "parameter": [ ... ],
#                         "parameter-value": [ ... ],
#                         "parameter-parameter": [ ... ]
#                     }
#                 }
#             }
#         }
#     }
# }

# # Examples

# **Input:**

# ***INPUT1:***

# {
#     "/v1/register": {
#         "post": {
#             "space1": {
#                 "satisfied-dependencies": "Minimum input space.",
#                 "subspace1": {
#                     "parameter": [
#                         "username",
#                         "password"
#                     ],
#                     "parameter-value": [],
#                     "parameter-parameter": []
#                 }
#             },
#             "space2": {
#                 "satisfied-dependencies": "Either the parameter email or phoneNumber must be provided.",
#                 "subspace1": {
#                     "parameter": [
#                         "email"
#                     ],
#                     "parameter-value": [],
#                     "parameter-parameter": []
#                 },
#                 "subspace2": {
#                     "parameter": [
#                         "phoneNumber"
#                     ],
#                     "parameter-value": [],
#                     "parameter-parameter": []
#                 },
#                 "error_space": {
#                     "error_space1": {
#                         "parameter": [
#                             "email",
#                             "phoneNumber"
#                         ],
#                         "parameter-value": [],
#                         "parameter-parameter": []
#                     }
#                 }
#             },
#             "space3": {
#                 "satisfied-dependencies": "The parameter confirmPassword must be equal to parameter password.",
#                 "subspace1": {
#                     "parameter": [
#                         "confirmPassword"
#                     ],
#                     "parameter-value": [],
#                     "parameter-parameter": [
#                         "confirmPassword = password"
#                     ]
#                 },
#                 "error_space": {
#                     "error_space1": {
#                         "parameter": [
#                             "confirmPassword"
#                         ],
#                         "parameter-value": [],
#                         "parameter-parameter": [
#                             "confirmPassword != password"
#                         ]
#                     }
#                 }
#             },
#             "space4": {
#                 "satisfied-dependencies": "If the value of parameter username is admin, the value of parameter password must be equal to 111",
#                 "subspace1": {
#                     "parameter": [],
#                     "parameter-value": [
#                         "username = admin",
#                         "password = 111"
#                     ],
#                     "parameter-parameter": []
#                 },
#                 "error_space": {
#                     "error_space1": {
#                         "parameter": [],
#                         "parameter-value": [
#                             "username = admin",
#                             "password != 111"
#                         ],
#                         "parameter-parameter": []
#                     }
#                 }
#             },
#             "space5": {
#                 "satisfied-dependencies": "Scalable space.",
#                 "involved-parameters": [
#                     "userInfo"
#                 ],
#                 "subspace1": {
#                     "parameter": [
#                         "userInfo"
#                     ],
#                     "parameter-value": [],
#                     "parameter-parameter": []
#                 }
#             }
#         }
#     },
#     "/v1/settingInformation": {
#         "get": {
#             "space1": {
#                 "satisfied-dependencies": "Minimum input space.",
#                 "subspace1": {
#                     "parameter": [
#                         "username"
#                     ],
#                     "parameter-value": [],
#                     "parameter-parameter": []
#                 }
#             }
#         }
#     }
# }

# ***INPUT2:***

# [
#     {
#         "parameter_name": "username",
#         "type": "string",
#         "required": true,
#         "format": [
#             "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,12}$",
#             "^admin$"
#         ],
#         "valid_input_space_categories": [
#             {
#                 "input_space_category": "Lowercase English letters and numbers",
#                 "description": "The parameter username only contains lowercase English letters and numbers.",
#                 "representative_samples": [
#                     "ui12934kj1",
#                     "12o310pazdc",
#                     "abcdefghijk1"
#                 ]
#             },
#             {
#                 "input_space_category": "Uppercase English letters and numbers",
#                 "description": "The parameter username contains only uppercase English letters and numbers.",
#                 "representative_samples": [
#                     "OSAGFJK123",
#                     "129011KAF"
#                 ]
#             },
#             {
#                 "input_space_category": "Uppercase and lowercase English letters and numbers",
#                 "description": "The parameter username contains only uppercase English letters, lowercase English letters and numbers.",
#                 "representative_samples": [
#                     "afK8HJas11",
#                     "918Knnna1II"
#                 ]
#             },
#             {
#                 "input_space_category": "Administrator account",
#                 "description": "The value of parameter username is the administrator account.",
#                 "representative_samples": [
#                     "admin"
#                 ]
#             }
#         ],
#         "invalid_input_space_categories": [
#             {
#                 "input_space_category": "Pure digital",
#                 "description": "Only contains numbers.",
#                 "representative_samples": [
#                     "1929120",
#                     "277345888"
#                 ]
#             },
#             {
#                 "input_space_category": "Pure English letters",
#                 "description": "Only contains English letters.",
#                 "representative_samples": [
#                     "aiojfgaAJJ",
#                     "KKGFOaap"
#                 ]
#             },
#             {
#                 "input_space_category": "invalid character",
#                 "description": "The string contains invalid characters.",
#                 "representative_samples": [
#                     "ok1235)_=1",
#                     ">awo??d"
#                 ]
#             }
#         ],
#         "operationId": null,
#         "url_path": "/v1/register",
#         "http_verb": "post"
#     },
#     {
#         "parameter_name": "password",
#         "type": "string",
#         "required": true,
#         "format": [
#             "^\\d{6}$",
#             "^111$"
#         ],
#         "valid_input_space_categories": [
#             {
#                 "input_space_category": "6-digit numerical string",
#                 "description": "6-digit numerical string.",
#                 "representative_samples": [
#                     "123456",
#                     "665324"
#                 ]
#             },
#             {
#                 "input_space_category": "Administrator password",
#                 "description": "The value of parameter password is the administrator password.",
#                 "representative_samples": [
#                     "111"
#                 ]
#             }
#         ],
#         "invalid_input_space_categories": [
#             {
#                 "input_space_category": "Non 6-digit numeric string",
#                 "description": "Non 6-digit numeric string.",
#                 "representative_samples": [
#                     "1929120",
#                     "277345888",
#                     "1200"
#                 ]
#             },
#             {
#                 "input_space_category": "Invalid characters",
#                 "description": "The parameter password contains invalid characters.",
#                 "representative_samples": [
#                     "123ka3",
#                     "99./oa"
#                 ]
#             }
#         ],
#         "operationId": null,
#         "url_path": "/v1/register",
#         "http_verb": "post"
#     },
#     {
#         "parameter_name": "email",
#         "type": "string",
#         "required": false,
#         "format": [
#             "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
#         ],
#         "valid_input_space_categories": [
#             {
#                 "input_space_category": "valid email format",
#                 "description": "The parameter email contains correct email formats.",
#                 "representative_samples": [
#                     "user@example.com",
#                     "hello.world@domain.co.uk"
#                 ]
#             }
#         ],
#         "invalid_input_space_categories": [
#             {
#                 "input_space_category": "invalid email format",
#                 "description": "The parameter email contains incorrect email formats.",
#                 "representative_samples": [
#                     "user@.example.com",
#                     "user@@example.com"
#                 ]
#             }
#         ],
#         "operationId": null,
#         "url_path": "/v1/register",
#         "http_verb": "post"
#     },
#     {
#         "parameter_name": "phoneNumber",
#         "type": "string",
#         "required": false,
#         "format": [
#             "^1[3-9]\\{9}$"
#         ],
#         "valid_input_space_categories": [
#             {
#                 "input_space_category": "valid phoneNumber format",
#                 "description": "The parameter phoneNumber contains correct phone number formats.",
#                 "representative_samples": [
#                     "13812345678",
#                     "19987654321"
#                 ]
#             }
#         ],
#         "invalid_input_space_categories": [
#             {
#                 "input_space_category": "invalid phoneNumber format",
#                 "description": "The parameter phoneNumber contains incorrect phone number formats.",
#                 "representative_samples": [
#                     "25123456789",
#                     "138123456789"
#                 ]
#             }
#         ],
#         "operationId": null,
#         "url_path": "/v1/register",
#         "http_verb": "post"
#     },
#     {
#         "parameter_name": "confirmPassword",
#         "type": "string",
#         "required": false,
#         "format": [
#             "^\\d{6}$"
#         ],
#         "valid_input_space_categories": [
#             {
#                 "input_space_category": "6-digit numerical string",
#                 "description": "6-digit numerical string.",
#                 "representative_samples": [
#                     "930256",
#                     "561134"
#                 ]
#             }
#         ],
#         "invalid_input_space_categories": [
#             {
#                 "input_space_category": "Non 6-digit numeric string",
#                 "description": "Non 6-digit numeric string.",
#                 "representative_samples": [
#                     "192912067895",
#                     "27788",
#                     "18"
#                 ]
#             },
#             {
#                 "input_space_category": "Invalid characters",
#                 "description": "The parameter password contains invalid characters.",
#                 "representative_samples": [
#                     "-=7/]}",
#                     ".;''ft"
#                 ]
#             }
#         ],
#         "operationId": null,
#         "url_path": "/v1/register",
#         "http_verb": "post"
#     },
#     {
#         "parameter_name": "userInfo",
#         "type": "string",
#         "required": false,
#         "format": [
#             "^[\\s\\S]*$"
#         ],
#         "valid_input_space_categories": [
#             {
#                 "input_space_category": "Short Text",
#                 "description": "A short text input for quick grammar checks.",
#                 "representative_samples": [
#                     "Hello world!",
#                     "This is an user information."
#                 ]
#             },
#             {
#                 "input_space_category": "Long Text",
#                 "description": "A longer text input for comprehensive grammar checks.",
#                 "representative_samples": [
#                     "Once upon a time, in a land far, far away, there lived a king who ruled with wisdom and kindness.",
#                     "In the midst of the bustling city, there was a small, quaint café that served the best coffee in town."
#                 ]
#             }
#         ],
#         "invalid_input_space_categories": [
#             {
#                 "input_space_category": "Non-String Input",
#                 "description": "Input that is not a string.",
#                 "representative_samples": [
#                     123,
#                     true,
#                     null
#                 ]
#             }
#         ],
#         "operationId": null,
#         "url_path": "/v1/register",
#         "http_verb": "post"
#     },
#     {
#         "parameter_name": "username",
#         "type": "string",
#         "required": true,
#         "format": [
#             "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,12}$"
#         ],
#         "valid_input_space_categories": [
#             {
#                 "input_space_category": "Lowercase English letters and numbers",
#                 "description": "The parameter username only contains lowercase English letters and numbers.",
#                 "representative_samples": [
#                     "1111aaaa"
#                 ]
#             },
#             {
#                 "input_space_category": "Uppercase English letters and numbers",
#                 "description": "The parameter username contains only uppercase English letters and numbers.",
#                 "representative_samples": [
#                     "1111AAAA"
#                 ]
#             },
#             {
#                 "input_space_category": "Uppercase and lowercase English letters and numbers",
#                 "description": "The parameter username contains only uppercase English letters, lowercase English letters and numbers.",
#                 "representative_samples": [
#                     "1111aaAA"
#                 ]
#             }
#         ],
#         "invalid_input_space_categories": [
#             {
#                 "input_space_category": "Pure digital",
#                 "description": "Only contains numbers.",
#                 "representative_samples": [
#                     "11111111"
#                 ]
#             },
#             {
#                 "input_space_category": "Pure English letters",
#                 "description": "Only contains English letters.",
#                 "representative_samples": [
#                     "aaaaAAAA"
#                 ]
#             },
#             {
#                 "input_space_category": "invalid character",
#                 "description": "The string contains invalid characters.",
#                 "representative_samples": [
#                     "././././"
#                 ]
#             }
#         ],
#         "operationId": null,
#         "url_path": "/v1/settingInformation",
#         "http_verb": "get"
#     }
# ]

# **Output:**

# {
#     "/v1/register": {
#         "post": {
#             "space1": {
#                 "satisfied-dependencies": "Minimum input space.",
#                 "subspace1": {
#                     "single-parameter-spaces": {
#                         "username": [
#                             {
#                                 "tag": "valid",
#                                 "type": "string",
#                                 "format": "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,12}$",
#                                 "input_space_category": "Lowercase English letters and numbers",
#                                 "description": "The parameter username only contains lowercase English letters and numbers.",
#                                 "representative_samples": [
#                                     "ui12934kj1",
#                                     "12o310pazdc",
#                                     "abcdefghijk1"
#                                 ]
#                             },
#                             {
#                                 "tag": "valid",
#                                 "type": "string",
#                                 "format": "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,12}$",
#                                 "input_space_category": "Uppercase English letters and numbers",
#                                 "description": "The parameter username contains only uppercase English letters and numbers.",
#                                 "representative_samples": [
#                                     "OSAGFJK123",
#                                     "129011KAF"
#                                 ]
#                             },
#                             {
#                                 "tag": "valid",
#                                 "type": "string",
#                                 "format": "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,12}$",
#                                 "input_space_category": "Uppercase and lowercase English letters and numbers",
#                                 "description": "The parameter username contains only uppercase English letters, lowercase English letters and numbers.",
#                                 "representative_samples": [
#                                     "afK8HJas11",
#                                     "918Knnna1II"
#                                 ]
#                             },
#                             {
#                                 "tag": "valid",
#                                 "type": "string",
#                                 "format": "^admin$",
#                                 "input_space_category": "Administrator account",
#                                 "description": "The value of parameter username is the administrator account.",
#                                 "representative_samples": [
#                                     "admin"
#                                 ]
#                             },
#                             {
#                                 "tag": "invalid",
#                                 "type": "string",
#                                 "format": null,
#                                 "input_space_category": "Pure digital",
#                                 "description": "Only contains numbers.",
#                                 "representative_samples": [
#                                     "1929120",
#                                     "277345888"
#                                 ]
#                             },
#                             {
#                                 "tag": "invalid",
#                                 "type": "string",
#                                 "format": null,
#                                 "input_space_category": "Pure English letters",
#                                 "description": "Only contains English letters.",
#                                 "representative_samples": [
#                                     "aiojfgaAJJ",
#                                     "KKGFOaap"
#                                 ]
#                             },
#                             {
#                                 "tag": "invalid",
#                                 "type": "string",
#                                 "format": null,
#                                 "input_space_category": "invalid character",
#                                 "description": "The string contains invalid characters.",
#                                 "representative_samples": [
#                                     "ok1235)_=1",
#                                     ">awo??d"
#                                 ]
#                             }
#                         ],
#                         "password": [
#                             {
#                                 "tag": "valid",
#                                 "type": "string",
#                                 "format": "^\\d{6}$",
#                                 "input_space_category": "6-digit numerical string",
#                                 "description": "6-digit numerical string.",
#                                 "representative_samples": [
#                                     "123456",
#                                     "665324"
#                                 ]
#                             },
#                             {
#                                 "tag": "valid",
#                                 "type": "string",
#                                 "format": "^111$",
#                                 "input_space_category": "Administrator password",
#                                 "description": "The value of parameter password is the administrator password.",
#                                 "representative_samples": [
#                                     "111"
#                                 ]
#                             },
#                             {
#                                 "tag": "invalid",
#                                 "type": "string",
#                                 "format": null,
#                                 "input_space_category": "Non 6-digit numeric string",
#                                 "description": "Non 6-digit numeric string.",
#                                 "representative_samples": [
#                                     "1929120",
#                                     "277345888",
#                                     "1200"
#                                 ]
#                             },
#                             {
#                                 "tag": "invalid",
#                                 "type": "string",
#                                 "format": null,
#                                 "input_space_category": "Invalid characters",
#                                 "description": "The parameter password contains invalid characters.",
#                                 "representative_samples": [
#                                     "123ka3",
#                                     "99./oa"
#                                 ]
#                             }
#                         ]
#                     },
#                     "parameter": [
#                         "username",
#                         "password"
#                     ],
#                     "parameter-value": [],
#                     "parameter-parameter": []
#                 }
#             },
#             "space2": {
#                 "satisfied-dependencies": "Either the parameter email or phoneNumber must be provided.",
#                 "subspace1": {
#                     "single-parameter-spaces": {
#                         "email": [
#                             {
#                                 "tag": "valid",
#                                 "type": "string",
#                                 "format": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
#                                 "input_space_category": "valid email format",
#                                 "description": "The parameter email contains correct email formats.",
#                                 "representative_samples": [
#                                     "user@example.com",
#                                     "hello.world@domain.co.uk"
#                                 ]
#                             },
#                             {
#                                 "tag": "invalid",
#                                 "type": "string",
#                                 "format": null,
#                                 "input_space_category": "invalid email format",
#                                 "description": "The parameter email contains incorrect email formats.",
#                                 "representative_samples": [
#                                     "user@.example.com",
#                                     "user@@example.com"
#                                 ]
#                             }
#                         ]
#                     },
#                     "parameter": [
#                         "email"
#                     ],
#                     "parameter-value": [],
#                     "parameter-parameter": []
#                 },
#                 "subspace2": {
#                     "single-parameter-spaces": {
#                         "phoneNumber": [
#                             {
#                                 "tag": "valid",
#                                 "type": "string",
#                                 "format": "^1[3-9]\\{9}$",
#                                 "input_space_category": "valid phoneNumber format",
#                                 "description": "The parameter phoneNumber contains correct phone number formats.",
#                                 "representative_samples": [
#                                     "13812345678",
#                                     "19987654321"
#                                 ]
#                             },
#                             {
#                                 "tag": "invalid",
#                                 "type": "string",
#                                 "format": null,
#                                 "input_space_category": "invalid phoneNumber format",
#                                 "description": "The parameter phoneNumber contains incorrect phone number formats.",
#                                 "representative_samples": [
#                                     "25123456789",
#                                     "138123456789"
#                                 ]
#                             }
#                         ]
#                     },
#                     "parameter": [
#                         "phoneNumber"
#                     ],
#                     "parameter-value": [],
#                     "parameter-parameter": []
#                 },
#                 "error_space": {
#                     "error_space1": {
#                         "single-parameter-spaces": {
#                             "email": [
#                                 {
#                                     "tag": "valid",
#                                     "type": "string",
#                                     "format": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
#                                     "input_space_category": "valid email format",
#                                     "description": "The parameter email contains correct email formats.",
#                                     "representative_samples": [
#                                         "user@example.com",
#                                         "hello.world@domain.co.uk"
#                                     ]
#                                 },
#                                 {
#                                     "tag": "invalid",
#                                     "type": "string",
#                                     "format": null,
#                                     "input_space_category": "invalid email format",
#                                     "description": "The parameter email contains incorrect email formats.",
#                                     "representative_samples": [
#                                         "user@.example.com",
#                                         "user@@example.com"
#                                     ]
#                                 }
#                             ],
#                             "phoneNumber": [
#                             {
#                                 "tag": "valid",
#                                 "type": "string",
#                                 "format": "^1[3-9]\\{9}$",
#                                 "input_space_category": "valid phoneNumber format",
#                                 "description": "The parameter phoneNumber contains correct phone number formats.",
#                                 "representative_samples": [
#                                     "13812345678",
#                                     "19987654321"
#                                 ]
#                             },
#                             {
#                                 "tag": "invalid",
#                                 "type": "string",
#                                 "format": null,
#                                 "input_space_category": "invalid phoneNumber format",
#                                 "description": "The parameter phoneNumber contains incorrect phone number formats.",
#                                 "representative_samples": [
#                                     "25123456789",
#                                     "138123456789"
#                                 ]
#                             }
#                         ]
#                         },
#                         "parameter": [
#                             "email",
#                             "phoneNumber"
#                         ],
#                         "parameter-value": [],
#                         "parameter-parameter": []
#                     }
#                 }
#             },
#             "space3": {
#                 "satisfied-dependencies": "The parameter confirmPassword must be equal to parameter password.",
#                 "subspace1": {
#                     "single-parameter-spaces": {
#                         "confirmPassword": [
#                             {
#                                 "tag": "valid",
#                                 "type": "string",
#                                 "format": "^\\d{6}$",
#                                 "input_space_category": "6-digit numerical string",
#                                 "description": "6-digit numerical string.",
#                                 "representative_samples": [
#                                     "930256",
#                                     "561134"
#                                 ]
#                             },
#                             {
#                                 "tag": "invalid",
#                                 "type": "string",
#                                 "format": null,
#                                 "input_space_category": "Non 6-digit numeric string",
#                                 "description": "Non 6-digit numeric string.",
#                                 "representative_samples": [
#                                     "192912067895",
#                                     "27788",
#                                     "18"
#                                 ]
#                             },
#                             {
#                                 "tag": "invalid",
#                                 "type": "string",
#                                 "format": null,
#                                 "input_space_category": "Invalid characters",
#                                 "description": "The parameter password contains invalid characters.",
#                                 "representative_samples": [
#                                     "-=7/]}",
#                                     ".;''ft"
#                                 ]
#                             }
#                         ],
#                         "password": [
#                             {
#                                 "tag": "valid",
#                                 "type": "string",
#                                 "format": "^\\d{6}$",
#                                 "input_space_category": "6-digit numerical string",
#                                 "description": "6-digit numerical string.",
#                                 "representative_samples": [
#                                     "123456",
#                                     "665324"
#                                 ]
#                             },
#                             {
#                                 "tag": "valid",
#                                 "type": "string",
#                                 "format": "^111$",
#                                 "input_space_category": "Administrator password",
#                                 "description": "The value of parameter password is the administrator password.",
#                                 "representative_samples": [
#                                     "111"
#                                 ]
#                             },
#                             {
#                                 "tag": "invalid",
#                                 "type": "string",
#                                 "format": null,
#                                 "input_space_category": "Non 6-digit numeric string",
#                                 "description": "Non 6-digit numeric string.",
#                                 "representative_samples": [
#                                     "1929120",
#                                     "277345888",
#                                     "1200"
#                                 ]
#                             },
#                             {
#                                 "tag": "invalid",
#                                 "type": "string",
#                                 "format": null,
#                                 "input_space_category": "Invalid characters",
#                                 "description": "The parameter password contains invalid characters.",
#                                 "representative_samples": [
#                                     "123ka3",
#                                     "99./oa"
#                                 ]
#                             }
#                         ]
#                     },
#                     "parameter": [
#                         "confirmPassword"
#                     ],
#                     "parameter-value": [],
#                     "parameter-parameter": [
#                         "confirmPassword = password"
#                     ]
#                 },
#                 "error_space": {
#                     "error_space1": {
#                         "single-parameter-spaces": {
#                             "confirmPassword": [
#                                 {
#                                     "tag": "valid",
#                                     "type": "string",
#                                     "format": "^\\d{6}$",
#                                     "input_space_category": "6-digit numerical string",
#                                     "description": "6-digit numerical string.",
#                                     "representative_samples": [
#                                         "930256",
#                                         "561134"
#                                     ]
#                                 },
#                                 {
#                                     "tag": "invalid",
#                                     "type": "string",
#                                     "format": null,
#                                     "input_space_category": "Non 6-digit numeric string",
#                                     "description": "Non 6-digit numeric string.",
#                                     "representative_samples": [
#                                         "192912067895",
#                                         "27788",
#                                         "18"
#                                     ]
#                                 },
#                                 {
#                                     "tag": "invalid",
#                                     "type": "string",
#                                     "format": null,
#                                     "input_space_category": "Invalid characters",
#                                     "description": "The parameter password contains invalid characters.",
#                                     "representative_samples": [
#                                         "-=7/]}",
#                                         ".;''ft"
#                                     ]
#                                 }
#                             ],
#                             "password": [
#                                 {
#                                     "tag": "valid",
#                                     "type": "string",
#                                     "format": "^\\d{6}$",
#                                     "input_space_category": "6-digit numerical string",
#                                     "description": "6-digit numerical string.",
#                                     "representative_samples": [
#                                         "123456",
#                                         "665324"
#                                     ]
#                                 },
#                                 {
#                                     "tag": "valid",
#                                     "type": "string",
#                                     "format": "^111$",
#                                     "input_space_category": "Administrator password",
#                                     "description": "The value of parameter password is the administrator password.",
#                                     "representative_samples": [
#                                         "111"
#                                     ]
#                                 },
#                                 {
#                                     "tag": "invalid",
#                                     "type": "string",
#                                     "format": null,
#                                     "input_space_category": "Non 6-digit numeric string",
#                                     "description": "Non 6-digit numeric string.",
#                                     "representative_samples": [
#                                         "1929120",
#                                         "277345888",
#                                         "1200"
#                                     ]
#                                 },
#                                 {
#                                     "tag": "invalid",
#                                     "type": "string",
#                                     "format": null,
#                                     "input_space_category": "Invalid characters",
#                                     "description": "The parameter password contains invalid characters.",
#                                     "representative_samples": [
#                                         "123ka3",
#                                         "99./oa"
#                                     ]
#                                 }
#                             ]
#                         },
#                         "parameter": [
#                             "confirmPassword"
#                         ],
#                         "parameter-value": [],
#                         "parameter-parameter": [
#                             "confirmPassword != password"
#                         ]
#                     }
#                 }
#             },
#             "space4": {
#                 "satisfied-dependencies": "If the value of parameter username is admin, the value of parameter password must be equal to 111",
#                 "subspace1": {
#                     "single-parameter-spaces": {
#                         "username": [
#                             {
#                                 "tag": "valid",
#                                 "type": "string",
#                                 "format": "^admin$",
#                                 "input_space_category": "Administrator account",
#                                 "description": "The value of parameter username is the administrator account.",
#                                 "representative_samples": [
#                                     "admin"
#                                 ]
#                             }
#                         ],
#                         "password": [
#                             {
#                                 "tag": "valid",
#                                 "type": "string",
#                                 "format": "^111$",
#                                 "input_space_category": "Administrator password",
#                                 "description": "The value of parameter password is the administrator password.",
#                                 "representative_samples": [
#                                     "111"
#                                 ]
#                             }
#                         ]
#                     },
#                     "parameter": [],
#                     "parameter-value": [
#                         "username = admin",
#                         "password = 111"
#                     ],
#                     "parameter-parameter": []
#                 },
#                 "error_space": {
#                     "error_space1": {
#                         "single-parameter-spaces": {
#                             "username": [
#                                 {
#                                     "tag": "valid",
#                                     "type": "string",
#                                     "format": "^admin$",
#                                     "input_space_category": "Administrator account",
#                                     "description": "The value of parameter username is the administrator account.",
#                                     "representative_samples": [
#                                         "admin"
#                                     ]
#                                 }
#                             ],
#                             "password": [
#                                 {
#                                     "tag": "valid",
#                                     "type": "string",
#                                     "format": "^\\d{6}$",
#                                     "input_space_category": "6-digit numerical string",
#                                     "description": "6-digit numerical string.",
#                                     "representative_samples": [
#                                         "123456",
#                                         "665324"
#                                     ]
#                                 },
#                                 {
#                                     "tag": "invalid",
#                                     "type": "string",
#                                     "format": null,
#                                     "input_space_category": "Non 6-digit numeric string",
#                                     "description": "Non 6-digit numeric string.",
#                                     "representative_samples": [
#                                         "1929120",
#                                         "277345888",
#                                         "1200"
#                                     ]
#                                 },
#                                 {
#                                     "tag": "invalid",
#                                     "type": "string",
#                                     "format": null,
#                                     "input_space_category": "Invalid characters",
#                                     "description": "The parameter password contains invalid characters.",
#                                     "representative_samples": [
#                                         "123ka3",
#                                         "99./oa"
#                                     ]
#                                 }
#                             ]
#                         },
#                         "parameter": [],
#                         "parameter-value": [
#                             "username = admin",
#                             "password != 111"
#                         ],
#                         "parameter-parameter": []
#                     }
#                 }
#             },
#             "space5": {
#                 "satisfied-dependencies": "Scalable space.",
#                 "involved-parameters": [
#                     "userInfo"
#                 ],
#                 "subspace1": {
#                     "single-parameter-spaces": {
#                         "userInfo": [
#                             {
#                                 "tag": "valid",
#                                 "type": "string",
#                                 "format": "^[\\s\\S]*$",
#                                 "input_space_category": "Short Text",
#                                 "description": "A short text input for quick grammar checks.",
#                                 "representative_samples": [
#                                     "Hello world!",
#                                     "This is an user information."
#                                 ]
#                             },
#                             {
#                                 "tag": "valid",
#                                 "type": "string",
#                                 "format": "^[\\s\\S]*$",
#                                 "input_space_category": "Long Text",
#                                 "description": "A longer text input for comprehensive grammar checks.",
#                                 "representative_samples": [
#                                     "Once upon a time, in a land far, far away, there lived a king who ruled with wisdom and kindness.",
#                                     "In the midst of the bustling city, there was a small, quaint café that served the best coffee in town."
#                                 ]
#                             }
#                         ]
#                     },
#                     "parameter": [
#                         "userInfo"
#                     ],
#                     "parameter-value": [],
#                     "parameter-parameter": []
#                 }
#             }
#         }
#     },
#     "/v1/settingInformation": {
#         "get": {
#             "space1": {
#                 "satisfied-dependencies": "Minimum input space.",
#                 "subspace1": {
#                     "single-parameter-spaces": {
#                         "username": [
#                             {
#                                 "tag": "valid",
#                                 "type": "string",
#                                 "format": "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,12}$",
#                                 "input_space_category": "Lowercase English letters and numbers",
#                                 "description": "The parameter username only contains lowercase English letters and numbers.",
#                                 "representative_samples": [
#                                     "1111aaaa"
#                                 ]
#                             },
#                             {
#                                 "tag": "valid",
#                                 "type": "string",
#                                 "format": "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,12}$",
#                                 "input_space_category": "Uppercase English letters and numbers",
#                                 "description": "The parameter username contains only uppercase English letters and numbers.",
#                                 "representative_samples": [
#                                     "1111AAAA"
#                                 ]
#                             },
#                             {
#                                 "tag": "valid",
#                                 "type": "string",
#                                 "format": "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,12}$",
#                                 "input_space_category": "Uppercase and lowercase English letters and numbers",
#                                 "description": "The parameter username contains only uppercase English letters, lowercase English letters and numbers.",
#                                 "representative_samples": [
#                                     "1111aaAA"
#                                 ]
#                             }
#                         ]
#                     },
#                     "parameter": [
#                         "username"
#                     ],
#                     "parameter-value": [],
#                     "parameter-parameter": []
#                 }
#             }
#         }
#     }
# }

# """.strip()