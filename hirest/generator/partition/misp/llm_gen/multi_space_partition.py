import json
from typing import Callable, List, Optional, Set

from hirest.generator.partition.misp.llm_gen.prompt_multi_space_partition_gen import  \
    PROMPT_MULTI_SPACE_PARTITION_final
from hirest.llm.openai import OpenAIChatLLM
from hirest.model.operation import Operation
from hirest.utils.RW_data import load_data
from hirest.utils.retry import retry


def _merge_partition_results(dst: dict, src: dict):
    for a, b in src.items():
        if a not in dst:
            dst[a] = b
        else:
            dst[a].update(b)


def multi_space_partition_gen(
    dep: dict,
    op_data_path: str,
    use_raw_doc_input: bool = False,
    completed_api_keys: Optional[Set[str]] = None,
    existing_results: Optional[dict] = None,
    on_api_done: Optional[Callable[[str, dict, dict], None]] = None,
) -> dict:

    results:dict = dict(existing_results or {})
    completed_api_keys = completed_api_keys or set()

    operation_data: List[Operation] = load_data(op_data_path)
    for idx, item in enumerate(operation_data, start=1):
        api_key = f"{item['raw_doc_slide']['method'].lower()} {item['raw_doc_slide']['path']}"
        if api_key in completed_api_keys:
            print(
                f"\n\33[34m[offline][INFO] Skip API {idx}/{len(operation_data)} (checkpoint hit): {api_key}\33[0m"
            )
            continue
        print(
            f"\n\33[34m[offline][INFO] Processing API {idx}/{len(operation_data)}: {item['raw_doc_slide']['method'].lower()} {item['raw_doc_slide']['path']}\33[0m"
        )
        param_data = json.dumps(item["param_list"])
        if use_raw_doc_input:
            single_input1 = item.get("raw_doc_slide", {})
        else:
            dep_info = dep.get(item['url'], {}).get(item['method'].lower(), {})
            all_dependencies = dep_info.get("all-dependencies", [])
            single_input1 = {
                item['url']: {
                    item['method'].lower(): all_dependencies
                }
            }

        single_task_prompt = f"""
    
        **Input:**
    
        ***INPUT1:***
    
        {single_input1}
    
        ***INPUT2:***
    
        {param_data}
    
        """.strip()

        LLM_MODEL: str = "gpt-5"
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
        _merge_partition_results(results, result)
        if on_api_done:
            on_api_done(api_key, result, results)
    #
    # print(f"\n[offline][INFO] {results}")
    return results