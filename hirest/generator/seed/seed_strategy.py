import json
import random
import re


# TODO: 4.2 ：
#  1.可能要在根据约束生成空间时，让LLM加入SAT表达式。
#  2.在选择空间时候，防止后选的空间对前面选的空间约束造成破坏
#       方法：每次choice维护两个集合：1.已经选择空间的约束信息的SAT集合。
#                                 2.已经选择空间中的单参数空间。
#            挑选空间时尝试把此时的subspace中的SAT表达式加入集合1，
#            是否会破坏之前的逻辑关系，若破坏，放弃选择，重选。若不破坏，
#            选择该空间，将该subspace的SAT逻辑表达式加入集合1，将选出
#            的单参数空间加入集合2，继续下一步挑选。


def collect_parameters(data):
    parameters = []

    if "parameter" in data:
        for p in data["parameter"]:
            parameters.append(p)

    if "parameter-value" in data:
        for expr in data["parameter-value"]:
            parts = expr.split()
            parameters.extend(parts)

    if "parameter-parameter" in data:
        for expr in data["parameter-parameter"]:
            parts = expr.split()
            parameters.extend(parts)
    return parameters

def seed_strategy_70percent(data: dict, times: int) -> dict:
    # 方法需要执行TIMES次选择，每次选择互不相关。每次选择时，
    # space1中的subspace1是必选的空间，首先拿到的就是该空间中的若干个信息。
    # 然后接着有60%的概率随机选择其他space空间，选过的space空间不再选择，
    # 若选择spaceX空间，那么再在spaceX的所有subspace和error_space中随机选择一个，
    # 若选到error_space，则再需要在error_space空间中随机选择一个error_space空间，
    # 将其中信息保存下来，这时space4就算选过了，不能再选。

    # !!! 该方法如果涉及空间很多的情况，空间n，全部空间同时作为输入空间的概率较低，0.6的n次方

    results = {}

    for path, methods in data.items():
        results[path] = {}  # 初始化路径

        for method, method_data in methods.items():

            method_seed = {"seeds": []}
            for choice_id in range(1, times + 1):
                # if choice_id <= times//2 : # generate error seed
                #     current_choice = {
                #         "tag": "error",
                #         "selected-spaces": ["space1-subspace1"],
                #         "selected-parameters-list": {},
                #         "parameter-parameter": []
                #     }
                #     selected_spaces = set()  # 存储已经选择过的空间
                #     selected_spaces.add("space1")
                #     parameter_list = collect_parameters(method_data["space1"]["subspace1"])
                #     current_choice["parameter-parameter"].extend(method_data["space1"]["subspace1"]["parameter-parameter"])
                #
                #     if parameter_list:
                #         for param in parameter_list:
                #             # if param not in method_data["space1"]["subspace1"]["single-parameter-spaces"] or not method_data["space1"]["subspace1"]["single-parameter-spaces"][param]:
                #             #     print(f"[WARNING] 参数 '{param}' 不在 single-parameter-spaces 中，跳过")
                #             #     continue
                #             current_choice["selected-parameters-list"][param] = random.choice(
                #                 method_data["space1"]["subspace1"]["single-parameter-spaces"][param])
                #
                #     """
                #     error seed must include one error_space at least.
                #     if not have error_space, the error space is same to valid space.
                #     """
                #     the_space_name_that_include_error_space = [space_name for space_name, space_content in method_data.items() if "error_space" in space_content]
                #     if the_space_name_that_include_error_space:
                #         error_space_choose = random.choice(the_space_name_that_include_error_space)
                #         selected_spaces.add(error_space_choose)
                #         error_subspace_list = [item for item in method_data[error_space_choose]["error_space"].keys()]
                #         error_subspace_choose = random.choice(error_subspace_list)
                #         param_list = collect_parameters(method_data[error_space_choose]["error_space"][error_subspace_choose])
                #         for param in param_list:
                #             current_choice["selected-parameters-list"][param] = random.choice(
                #                 method_data[error_space_choose]["error_space"][error_subspace_choose][
                #                     "single-parameter-spaces"][param])
                #         current_choice["parameter-parameter"].extend(
                #             method_data[error_space_choose]["error_space"][error_subspace_choose]["parameter-parameter"])
                #         current_choice["selected-spaces"].append(f"{error_space_choose}-error_space-{error_subspace_choose}")
                #
                #
                #
                #     while random.random() < 0.7:
                #         space_rest = [spaceX for spaceX in method_data.keys() if spaceX not in selected_spaces]
                #         if not space_rest:
                #             break
                #         space_selected = random.choice(space_rest)
                #         selected_spaces.add(space_selected)
                #         subspace_list = [subspaceX for subspaceX in method_data[space_selected].keys() if
                #                          subspaceX.startswith("subspace")]
                #         error_subspace_list = []
                #         if "error_space" in method_data[space_selected]:
                #             error_subspace_list.extend(
                #                 [error_spaceX for error_spaceX in method_data[space_selected]["error_space"].keys()])
                #
                #         all_subspace_list = subspace_list + error_subspace_list
                #
                #         subspace_selected = random.choice(all_subspace_list)
                #         if subspace_selected.startswith("subspace"):
                #             param_list = collect_parameters(method_data[space_selected][subspace_selected])
                #             for param in param_list:
                #                 # if param not in method_data[space_selected][subspace_selected]["single-parameter-spaces"] or not method_data[space_selected][subspace_selected]["single-parameter-spaces"][param]:
                #                 #     print(f"[WARNING] 参数 '{param}' 不在 single-parameter-spaces 中，跳过")
                #                 #     continue
                #                 current_choice["selected-parameters-list"][param] = random.choice(
                #                     method_data[space_selected][subspace_selected]["single-parameter-spaces"][param])
                #             current_choice["parameter-parameter"].extend(
                #                 method_data[space_selected][subspace_selected]["parameter-parameter"])
                #             current_choice["selected-spaces"].append(f"{space_selected}-{subspace_selected}")
                #         else:
                #             param_list = collect_parameters(method_data[space_selected]["error_space"][subspace_selected])
                #             for param in param_list:
                #                 # if param not in method_data[space_selected]["error_space"][subspace_selected]["single-parameter-spaces"] or not method_data[space_selected]["error_space"][subspace_selected]["single-parameter-spaces"][param]:
                #                 #     print(f"[WARNING] 参数 '{param}' 不在 single-parameter-spaces 中，跳过")
                #                 #     continue
                #                 current_choice["selected-parameters-list"][param] = random.choice(
                #                     method_data[space_selected]["error_space"][subspace_selected][
                #                         "single-parameter-spaces"][param])
                #             current_choice["parameter-parameter"].extend(
                #                 method_data[space_selected]["error_space"][subspace_selected]["parameter-parameter"])
                #             current_choice["selected-spaces"].append(f"{space_selected}-error_space-{subspace_selected}")
                #     method_seed["seeds"].append(current_choice)
                # else:
                #     current_choice = {
                #         "tag": "valid",
                #         "selected-spaces": ["space1-subspace1"],
                #         "selected-parameters-list": {},
                #         "parameter-parameter": []
                #     }
                #     selected_spaces = set()
                #     selected_spaces.add("space1")
                #     parameter_list = collect_parameters(method_data["space1"]["subspace1"])
                #     current_choice["parameter-parameter"].extend(
                #         method_data["space1"]["subspace1"]["parameter-parameter"])
                #
                #     if parameter_list:
                #         for param in parameter_list:
                #             # if param not in method_data["space1"]["subspace1"]["single-parameter-spaces"] or not method_data["space1"]["subspace1"]["single-parameter-spaces"][param]:
                #             #     print(f"[WARNING] 参数 '{param}' 不在 single-parameter-spaces 中，跳过")
                #             #     continue
                #             current_choice["selected-parameters-list"][param] = random.choice(
                #                 method_data["space1"]["subspace1"]["single-parameter-spaces"][param])
                #
                #     while random.random() < 0.6:
                #         space_rest = [spaceX for spaceX in method_data.keys() if spaceX not in selected_spaces]
                #         if not space_rest:
                #             break
                #         space_selected = random.choice(space_rest)
                #         selected_spaces.add(space_selected)
                #         subspace_list = [subspaceX for subspaceX in method_data[space_selected].keys() if
                #                          subspaceX.startswith("subspace")]
                #
                #         all_subspace_list = subspace_list
                #
                #         subspace_selected = random.choice(all_subspace_list)
                #         param_list = collect_parameters(method_data[space_selected][subspace_selected])
                #         for param in param_list:
                #             # if param not in method_data[space_selected][subspace_selected]["single-parameter-spaces"] or not method_data[space_selected][subspace_selected]["single-parameter-spaces"][param]:
                #             #     print(f"[WARNING] 参数 '{param}' 不在 single-parameter-spaces 中，跳过")
                #             #     continue
                #             current_choice["selected-parameters-list"][param] = random.choice(
                #                 method_data[space_selected][subspace_selected]["single-parameter-spaces"][param])
                #         current_choice["parameter-parameter"].extend(
                #             method_data[space_selected][subspace_selected]["parameter-parameter"])
                #         current_choice["selected-spaces"].append(f"{space_selected}-{subspace_selected}")
                #     method_seed["seeds"].append(current_choice)

                """
                update: update all seed just have subspace, dont have error_space.
                """

                current_choice = {
                    "tag": "normal",
                    "selected-spaces": ["space1-subspace1"],
                    "selected-parameters-list": {},
                    "parameter-parameter": []
                }
                selected_spaces = set()  # 存储已经选择过的空间
                selected_spaces.add("space1")
                parameter_list = collect_parameters(method_data["space1"]["subspace1"])
                current_choice["parameter-parameter"].extend(method_data["space1"]["subspace1"]["parameter-parameter"])

                if parameter_list:
                    for param in parameter_list:
                        single_param_spaces = method_data["space1"]["subspace1"].get(
                            "single-parameter-spaces", {})
                        if param not in single_param_spaces:
                            continue  # 如果不存在则跳过
                        current_choice["selected-parameters-list"][param] = random.choice([
                            item for item in
                            method_data["space1"]["subspace1"]["single-parameter-spaces"][param]
                            if item.get("tag") == "valid"
                        ])

                while random.random() < 0.7:
                    space_rest = [spaceX for spaceX in method_data.keys() if spaceX not in selected_spaces]
                    if not space_rest:
                        break
                    space_selected = random.choice(space_rest)
                    selected_spaces.add(space_selected)
                    subspace_list = [subspaceX for subspaceX in method_data[space_selected].keys() if
                                     subspaceX.startswith("subspace")]

                    all_subspace_list = subspace_list

                    subspace_selected = random.choice(all_subspace_list)

                    param_list = collect_parameters(method_data[space_selected][subspace_selected])
                    if param_list:
                        for param in param_list:
                            single_param_spaces = method_data[space_selected][subspace_selected].get(
                                "single-parameter-spaces", {})
                            if param not in single_param_spaces:
                                continue  # 如果不存在则跳过
                            current_choice["selected-parameters-list"][param] = random.choice([
                                item for item in
                                method_data[space_selected][subspace_selected]["single-parameter-spaces"][param]
                                if item.get("tag") == "valid"
                            ])
                    if "parameter-parameter" in method_data[space_selected][subspace_selected]:
                        current_choice["parameter-parameter"].extend(
                            method_data[space_selected][subspace_selected]["parameter-parameter"])
                    current_choice["selected-spaces"].append(f"{space_selected}-{subspace_selected}")
                method_seed["seeds"].append(current_choice)
            results[path][method] = method_seed
    return results



