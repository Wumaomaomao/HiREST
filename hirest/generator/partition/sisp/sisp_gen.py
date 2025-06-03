import json
import os
from typing import List

from hirest.generator.partition.sisp.llm_gen.single_space_partition import \
    single_space_partition_gen_every
from hirest.model.sisp import SISP, SISP_SS


class SISPGenerator:
    """SISP Generator class: responsible for generating single input single partition (SISP) of each parameter."""

    def __init__(self, operation_data_path: str, llm_und_data: list):
        # Multi-parameter module need use it self.sisp_pre_data.
        self.sisp_pre_data: list = single_space_partition_gen_every(operation_data_path, llm_und_data)

    def save_list_SISP(self, output_path: str):
        data: List[SISP] = self.sisp_gen()
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([d.model_dump() for d in data], f, indent=4, ensure_ascii=False)

    def sisp_gen(self) -> List[SISP]:
        result: List[SISP] = []
        for SISP_item in self.sisp_pre_data:
            valid_list: List[SISP_SS] = []
            invalid_list: List[SISP_SS] = []
            for valid_list_item in SISP_item["valid_input_space_categories"]:
                valid_SISP_SS = SISP_SS(
                    param_name = SISP_item["parameter_name"],
                    category = valid_list_item["input_space_category"],
                    description = valid_list_item["description"],
                    samples = valid_list_item["representative_samples"],
                )
                valid_list.append(valid_SISP_SS)
            for valid_list_item in SISP_item["invalid_input_space_categories"]:
                valid_SISP_SS = SISP_SS(
                    param_name = SISP_item["parameter_name"],
                    category = valid_list_item["input_space_category"],
                    description = valid_list_item["description"],
                    samples = valid_list_item["representative_samples"],
                )
                invalid_list.append(valid_SISP_SS)
            SISP_data = SISP(
                op_name = f"{SISP_item['http_verb'].lower()} {SISP_item['url_path']}",
                type = SISP_item['type'],
                param_name = SISP_item['parameter_name'],
                format = SISP_item['format'],
                valid = valid_list,
                invalid = invalid_list,
            )
            result.append(SISP_data)
        return result