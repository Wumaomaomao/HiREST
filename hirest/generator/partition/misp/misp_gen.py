import json
import os
import logging
from threading import main_thread
from typing import List

from hirest.generator.partition.misp.llm_gen.mixed_space_partition import mixed_space_partition_gen
from hirest.generator.partition.misp.llm_gen.multi_space_partition import multi_space_partition_gen
from hirest.model.misp import MISP, Subspace, MixedSingleSpace, MISP_SS

logger = logging.getLogger(__name__)

class MISPGenerator:
    """MISP Generator class: responsible for generating multiple input space partition (MISP) of each operation."""

    # def __init__(
    #         self,
    #         single_space_file_path: str
    # ):
    def __init__(
            self,
            swagger_llm_extract_dep: dict,
            operation_data_path: str,
            # single_space_data is first version single_parameter_space_data
            # single_space_data = sisp_gen.sisp_pre_data

            single_space_data: list
        ):
        self.operation_data_path = operation_data_path
        self.swagger_llm_extract_dep = swagger_llm_extract_dep
        self.single_space_data = single_space_data
        # The multi-space-partition.json
        self.multi_space_partition_data : dict = []
        # The mixed-space-partition.json
        self.mixed_space_partition_data : dict = []
    

    def generate_multi_space_partition(self):
        self.multi_space_partition_data : dict = multi_space_partition_gen(self.swagger_llm_extract_dep, self.operation_data_path)
        logger.info(f"Successfully generated multi-space partition data.")
        logger.info(f"multi_space_partition results: {json.dumps(self.multi_space_partition_data, indent=4)}")

    def generate_mixed_space_partition(self):
        self.mixed_space_partition_data : dict = mixed_space_partition_gen(self.multi_space_partition_data, self.single_space_data)
        logger.info(f"Successfully generated mixed-space partition data.")
        logger.info(f"mixed_space_partition results: {json.dumps(self.mixed_space_partition_data, indent=4)}")

    def save_List_MISP(self, output_path: str):
        data: List[MISP] = self.misp_gen()
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([d.model_dump() for d in data], f, indent=4, ensure_ascii=False)


    def misp_gen(self) -> List[MISP]:
        """
        Generate MISP for each operation.
        @return MISP
            MISP objects.
        """
        misp_list : List[MISP] = []

        for path, methods in self.mixed_space_partition_data.items():
            for method, spaces in methods.items():
                op_name = f"{method} {path}"
                misp = MISP(
                    op_name = op_name,
                    space_list = [],
                )
                for space_name, space_content in spaces.items():
                    satisfied_dependencies : str = space_content.get("satisfied-dependencies", "")
                    involved_parameters : List[str] = space_content.get("involved-parameters", [])
                    subspace_list : List[Subspace] = []
                    for subspace_name, subspace_content in space_content.items():
                        if subspace_name == "satisfied-dependencies" or subspace_name == "error_space" or subspace_name == "involved-parameters":
                            continue
                        if not isinstance(subspace_content, dict) or "single-parameter-spaces" not in subspace_content:
                            continue
                        single_parameter_spaces_raw : dict = subspace_content["single-parameter-spaces"]
                        single_parameter_spaces : dict = {}
                        for param, space_items in single_parameter_spaces_raw.items():
                            space_objs = [MixedSingleSpace(**item) for item in space_items]
                            single_parameter_spaces[param] = space_objs
                        subspace = Subspace(
                            subspace_name = subspace_name,
                            single_parameter_spaces = single_parameter_spaces,
                            parameter = subspace_content.get("parameter", []),
                            parameter_value = subspace_content.get("parameter-value", []),
                            parameter_parameter = subspace_content.get("parameter-parameter", []),
                        )
                        subspace_list.append(subspace)
                    if "error_space" in space_content:
                        error_spaces = space_content["error_space"]
                        for error_name, error_content in error_spaces.items():
                            if not isinstance(error_content, dict) or "single-parameter-spaces" not in error_content:
                                continue
                            single_parameter_spaces_raw: dict = error_content["single-parameter-spaces"]
                            single_parameter_spaces: dict = {}
                            for param, space_items in single_parameter_spaces_raw.items():
                                space_objs = [MixedSingleSpace(**item) for item in space_items]
                                single_parameter_spaces[param] = space_objs
                            error_subspace = Subspace(
                                subspace_name = error_name,
                                single_parameter_spaces = single_parameter_spaces,
                                parameter = error_content.get("parameter", []),
                                parameter_value = error_content.get("parameter-value", []),
                                parameter_parameter = error_content.get("parameter-parameter", []),
                            )
                            subspace_list.append(error_subspace)
                    misp_ss = MISP_SS(
                        space_name = space_name,
                        satisfied_dependencies = satisfied_dependencies,
                        involved_parameters = involved_parameters,
                        subspace_list = subspace_list,
                    )
                    misp.space_list.append(misp_ss)
                misp_list.append(misp)
        return misp_list

