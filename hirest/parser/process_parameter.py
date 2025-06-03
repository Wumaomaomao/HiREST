import re
from typing import List

from hirest.model.parameter import Parameter


def give_param_type(data: dict, path: str, method: str) -> List[Parameter]:
    param_list = []
    method_details = data[path][method]
    path_params = re.findall(r"{(.*?)}", path)

    for detail in method_details .get("parameters", []):
        param_information = Parameter(
            param_name = detail.get("name"),
            param_type = "path" if detail.get("name") in path_params else "query",
            val_type = detail.get("type"),
            is_required =  detail.get("required"),
            description = detail.get("description")
        )
        param_list.append(param_information)
    for detail in method_details.get("requestBody", []):
        param_information = Parameter(
            param_name = detail.get("name"),
            param_type = "body",
            val_type = detail.get("type"),
            is_required = detail.get("required"),
            description = detail.get("description")
        )
        param_list.append(param_information)

    return param_list