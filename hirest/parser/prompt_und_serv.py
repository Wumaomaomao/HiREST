#
# # Role
# 你是一个资深的软件开发工程师，你精通于理解软件功能需求。
# # Goal
# 你需要基于提供的swagger片段，猜测这个系统完成什么功能逻辑。
# # Instruction
# 1.给出的swagger片段只包含服务级别的信息，不包含paths和components等具体路径参数信息，你需要理解服务级别的summary，description等包含自然语言描述信息。
# # Output Format
# # Examples

prompt_output_serv = """
Only return a string without any JSON or Markdown format as follow:

This service is mainly related to products and may be an internal system of a supermarket to complete product queries, deletions, etc.
""".strip()
prompt_example_serv = """
**Input:**

{
    "swagger": "2.0",
    "info": {
        "version": "1.0.0",
        "title": "Book Management API",
        "description": "A simple API for managing books in a library"
    },
    "host": "api.example.com",
    "basePath": "/v1",
    "schemes": ["https"]
}

**Output:**

This service is mainly related to book management and can be used for the library's book management system.
""".strip()

PROMPT_UND_serv = f"""

# Role

You are a senior software development engineer who is proficient in understanding software functional requirements.

# Goal

You need to guess what functional logic each API completes based on the provided swagger fragments and API interface list.

# Instruction

The given swagger fragment (JSON format) only contains service level information and does not include specific path parameter information such as paths and components. You need to understand that service level summaries, descriptions, etc. contain natural language description information.

# Output Format

{prompt_output_serv}

# Examples

{prompt_example_serv}

""".strip()