import json
import os
from typing import List, Optional

from hirest.generator.seed.seed_strategy import seed_strategy_70percent_valid_intersection
from hirest.model.misp import MixedSingleSpace
from hirest.model.seed import SeedModel

class Seed:
    """Seed Class: reponsible for generating randon initial test cases for fuzzing pool"""

    def __init__(self, mixed_space_data: dict, size: Optional[int]):
        """
        :param size: 用于设置种子空间大小，如果为 None 或非法值，则默认为 8
        :param mixed_space_data: 混合空间数据
        """
        if size is None or not isinstance(size, int) or size <= 1 or size > 10:
            self.seed_size = 8
        else:
            self.seed_size = size
        self.mixed_space_data = mixed_space_data

    def select_space(self) -> dict:
        space_selected = seed_strategy_70percent_valid_intersection(self.mixed_space_data, self.seed_size)

        return space_selected
    def gen_seed(self) -> List[SeedModel]:

        result : List[SeedModel] = []

        space_selected_data = self.select_space()

        for path, methods in space_selected_data.items():
            for method, content in methods.items():
                op_name = f"{method} {path}"
                for seed in content.get("seeds", []):
                    tag = seed.get("tag")
                    selected_spaces = seed.get("selected-spaces")
                    parameter_parameter = seed.get("parameter-parameter")
                    raw_params = seed.get("selected-parameters-list")

                    selected_parameters_list = {}
                    for param_name, param_content in raw_params.items():
                        # 构造 MixedSingleSpace 模型
                        space = MixedSingleSpace(**param_content)
                        selected_parameters_list[param_name] = space

                    seed_model = SeedModel(
                        op_name=op_name,
                        tag=tag,
                        selected_spaces=selected_spaces,
                        selected_parameters_list=selected_parameters_list,
                        parameter_parameter=parameter_parameter
                    )
                    result.append(seed_model)

        return result
    def save_seeds(self, output_path: str):
        data: List[SeedModel] = self.gen_seed()
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([d.model_dump() for d in data], f, indent=4, ensure_ascii=False)