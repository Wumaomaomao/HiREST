from hirest.llm.openai import OpenAIChatLLM
from hirest.parser.prompt_extract_dep import PROMPT_UND_API_m
from hirest.utils.retry import retry

def fix(src_data: dict, data: dict):

    for path, methods in src_data.get("paths", {}).items():
        if path not in data:
            data[path] = {}

        for method in methods:
            method = method.lower()
            if method not in data[path]:
                data[path][method] = {
                    "all-dependencies": []
                }

def get_swagger_understanding_m(data: dict) -> dict:

    paths = data.get("paths", {})

    single_task_prompt = f"""

    **Input:**

    {paths}

    """.strip()

    LLM_MODEL: str = "gpt-4o"
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": PROMPT_UND_API_m,
        },
        {
            "role": "user",
            "content": "Next, I will provide you with an input, please output it:\n" + single_task_prompt,
        },
    ]

    resp = OpenAIChatLLM(LLM_MODEL).invoke(messages)
    result = retry(resp, 1)
    fix(data, result) # 对于不存在依赖关系的API方法，大模型可能不会生成对应的path和method，对缺失的path和method进行补全。

    print(f"\n\033[34m[offline][INFO] llm understand for misp:\033[0m\n{result}")
    return result
