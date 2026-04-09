import json
import logging

from hirest.generator.partition.misp.llm_gen.prompt_mixed_space_partition_gen import part1, part2, \
    PROMPT_MIXED_SPACE_PARTITION_final
from hirest.llm.openai import OpenAIChatLLM
from hirest.utils.retry import retry

logger = logging.getLogger(__name__)
def mixed_space_partition_gen(multi: dict, single_space_data: list) -> dict:

    results: dict = {}
    sum_api = 0
    for path, methods in multi.items():
        for method in methods.items():
            sum_api += 1
    now = 1
    for path, methods in multi.items():
        for method, content in methods.items():
            method = method.lower()
            print(
                f"\n\33[34m[offline][INFO] Processing API (mixed) {now}/{sum_api}: {method.lower()} {path}\33[0m"
            )
            now += 1
            single_api = {
                path: {
                    method: content
                }
            }
            parameter_single_space_list = []
            now_path_and_method = f"{method.lower()} {path}"

            for item in single_space_data:
                if now_path_and_method == f"{item['http_verb'].lower()} {item['url_path']}":
                    valid_only_item = dict(item)
                    valid_only_item.pop("invalid_input_space_categories", None)
                    parameter_single_space_list.append(valid_only_item)

            logger.info(f"Prepared single space input: {parameter_single_space_list} for API: {method.lower()} {path}")

            single_task_prompt = f"""
            **Input:**
        
            ***INPUT1:***
        
            {single_api}
        
            ***INPUT2:***
        
            {parameter_single_space_list}
        
            """.strip()

            LLM_MODEL: str = "gpt-5"
            messages: list[dict[str, str]] = [
                {
                    "role": "system",
                    "content": PROMPT_MIXED_SPACE_PARTITION_final,
                },
                {
                    "role": "user",
                    "content": "Next, I will provide you with an input, please output it:\n" + single_task_prompt,
                },
            ]

            resp = OpenAIChatLLM(LLM_MODEL).invoke(messages)
            result = retry(resp,1)
            for a, b in result.items():
                if a not in results:
                    results[a] = b
                else:
                    results[a].update(b)

    return results