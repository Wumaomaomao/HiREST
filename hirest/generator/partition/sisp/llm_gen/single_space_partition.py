import json
from typing import Callable, List, Optional, Set

from hirest.generator.partition.sisp.llm_gen.prompt_fix_sisp import PROMPT_FIX
from hirest.generator.partition.sisp.llm_gen.prompt_single_space_partition_gen import \
    PROMPT_SINGLE_SPACE_PARTITION_final
from hirest.llm.openai import OpenAIChatLLM
from hirest.model.operation import Operation
from hirest.utils.RW_data import load_data
from hirest.utils.retry import retry

def fix_sisp(data: list, op_data: List[Operation]) -> list:

    need_to_fix_list = []
    need_to_fix_doc_slide_data: List = []
    for item in op_data:
        method = item["method"]
        url = item["url"]
        for param_item in item["param_list"]:
            p_name = param_item["param_name"]
            ok_exists = False
            for llm_item in data:
                if llm_item["parameter_name"] == p_name \
                    and llm_item["url_path"] == url \
                    and llm_item["http_verb"].lower() == method.lower():
                    ok_exists = True
                    break
            if not ok_exists:
                need_to_fix_list.append({
                    "method": method,
                    "url": url,
                    "param_name": p_name,
                })
                if item["raw_doc_slide"] not in need_to_fix_doc_slide_data:
                    need_to_fix_doc_slide_data.append(item["raw_doc_slide"])
            else: continue

    if not need_to_fix_list:
        return data
    else:
        print("Repairing data...")
        JSON_data1 = json.dumps(data)
        JSON_data2 = json.dumps(need_to_fix_list)
        JSON_data3 = json.dumps(need_to_fix_doc_slide_data)

        single_task_prompt = f"""

        **Input:**

        ***INPUT1:***

        {JSON_data1}

        ***INPUT2:***

        {JSON_data2}
        
        ***INPUT3:***

        {JSON_data3}

        """.strip()

        LLM_MODEL: str = "gpt-4o"
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": PROMPT_FIX,
            },
            {
                "role": "user",
                "content": "Next, I will provide you with an input, please output it:\n" + single_task_prompt,
            },
        ]

        resp = OpenAIChatLLM(LLM_MODEL).invoke(messages)
        fix_result = retry(resp, 0)

        return data + fix_result

def single_space_partition_gen_every(
    operation_data_path: str,
    llm_und_data: list,
    completed_api_keys: Optional[Set[str]] = None,
    existing_results: Optional[list] = None,
    on_api_done: Optional[Callable[[str, list, list], None]] = None,
) -> list:
    result = list(existing_results or [])
    completed_api_keys = completed_api_keys or set()
    operation_data: List[Operation] = load_data(operation_data_path)
    for idx, item in enumerate(operation_data, start=1):
        api_key = f"{item['raw_doc_slide']['method'].lower()} {item['raw_doc_slide']['path']}"
        if api_key in completed_api_keys:
            print(
                f"\n\33[34m[offline][INFO] Skip API {idx}/{len(operation_data)} (checkpoint hit): {api_key}\33[0m"
            )
            continue
        print(f"\n\33[34m[offline][INFO] Processing API {idx}/{len(operation_data)}: {item['raw_doc_slide']['method'].lower()} {item['raw_doc_slide']['path']}\33[0m")
        param_data = json.dumps(item["param_list"])
        target_api_name = api_key
        matched = next(
            (
                api_item
                for api_item in (llm_und_data or [])
                if isinstance(api_item, dict)
                and (api_item.get("api_name") or api_item.get("api_name:")) == target_api_name
            ),
            None,
        )
        llm_und = json.dumps(matched)
        single_task_prompt = f"""

        **Input:**
        
        ***INPUT1:***
        
        {llm_und}
        
        ***INPUT2:***
        
        {param_data}

        """.strip()

        LLM_MODEL: str = "gpt-5"
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": PROMPT_SINGLE_SPACE_PARTITION_final,
            },
            {
                "role": "user",
                "content": "Next, I will provide you with an input, please output it:\n" + single_task_prompt,
            },
        ]

        resp = OpenAIChatLLM(LLM_MODEL).invoke(messages)
        result1 = retry(resp, 0)
        result.extend(result1)
        if on_api_done:
            on_api_done(api_key, result1, result)

    return result
