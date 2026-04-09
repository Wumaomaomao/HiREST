from hirest.llm.openai import OpenAIChatLLM
from hirest.parser.prompt_und_api import PROMPT_UND_API_s
from hirest.utils.retry import retry


def get_swagger_understanding_s(data: dict, service_knowl: str) -> list:
    """
    读取 Swagger 的 paths 字段，生成适合 prompt 的多个 Input 片段，每个为一个 path+method。
    """
    results : list = []

    paths = data.get("paths", {})

    for path, methods in paths.items():
        for method, content in methods.items():
            method = method.lower()
            single_api = {
                path: {
                    method: content
                }
            }
            single_api_task_prompt = f"""

                **Input:**
                
                ***INPUT1:***
                
                {single_api}
                
                ***INPUT2:***
                
                {service_knowl}

                """.strip()

            LLM_MODEL: str = "gpt-5"
            messages: list[dict[str, str]] = [
                {
                    "role": "system",
                    "content": PROMPT_UND_API_s,
                },
                {
                    "role": "user",
                    "content": "Next, I will provide you with an input, please output it:\n" + single_api_task_prompt,
                },
            ]

            resp = OpenAIChatLLM(LLM_MODEL).invoke(messages)
            result = retry(resp, 1)

            # Normalize occasional key typo from LLM outputs (e.g., "api_name:").
            if isinstance(result, dict):
                if "api_name" not in result and "api_name:" in result:
                    result["api_name"] = result.pop("api_name:")
            results.append(result)

    print(f"\n\033[34m[offline][INFO] llm understand for sisp:\033[0m\n{results}")
    return results