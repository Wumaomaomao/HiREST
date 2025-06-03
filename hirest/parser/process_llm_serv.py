from hirest.llm.openai import OpenAIChatLLM
from hirest.parser.prompt_und_serv import PROMPT_UND_serv
from hirest.utils.retry import retry


def get_swagger_understanding_service(data: dict) -> str:
    keys_to_remove = ["paths", "components", "definitions"]
    clean_data = {k: v for k, v in data.items() if k not in keys_to_remove}

    single_api_task_prompt = f"""

    **Input:**

    ***INPUT1:***
    
    {clean_data}

    """.strip()

    LLM_MODEL: str = "gpt-4o"
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": PROMPT_UND_serv,
        },
        {
            "role": "user",
            "content": "Next, I will provide you with an input, please output it:\n" + single_api_task_prompt,
        },
    ]

    resp = OpenAIChatLLM(LLM_MODEL).invoke(messages)
    print(f"\n\033[34m[offline][INFO] llm understand for service:\033[0m\n{resp}")
    return resp
