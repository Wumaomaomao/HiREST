import json
from typing import List

from hirest.generator.partition.misp.llm_gen.prompt_multi_space_partition_gen import  \
    PROMPT_MULTI_SPACE_PARTITION_final
from hirest.llm.openai import OpenAIChatLLM
from hirest.model.operation import Operation
from hirest.utils.RW_data import load_data
from hirest.utils.retry import retry


def multi_space_partition_gen(dep: dict, op_data_path: str) -> dict:

    results:dict = {}

    operation_data: List[Operation] = load_data(op_data_path)
    for idx, item in enumerate(operation_data, start=1):
        print(
            f"\n\33[34m[offline][INFO] Processing API {idx}/{len(operation_data)}: {item['raw_doc_slide']['method'].lower()} {item['raw_doc_slide']['path']}\33[0m"
        )
        param_data = json.dumps(item["param_list"])
        dep_info = dep.get(item['url'], {}).get(item['method'].lower(), {})
        all_dependencies = dep_info.get("all-dependencies", [])

        single_llm_dep = {
            item['url']: {
                item['method'].lower(): all_dependencies
            }
        }

        single_task_prompt = f"""
    
        **Input:**
    
        ***INPUT1:***
    
        {single_llm_dep}
    
        ***INPUT2:***
    
        {param_data}
    
        """.strip()

        LLM_MODEL: str = "gpt-4o"
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": PROMPT_MULTI_SPACE_PARTITION_final,
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
    #
    # print(f"\n[offline][INFO] {results}")
    return results