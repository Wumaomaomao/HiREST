import json
import os
import re

from hirest.parser.preparser.preparser import PreParser

"""
4.18 update ok to generate array and object type parameter
"""

class Preprocess:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_data_no_ref = PreParser(file_path).parsed_ref_data


    def run(self) -> dict:

        """
        example_output is oas-constraint.json
        """
        example_output = {}

        paths = self.file_data_no_ref.get("paths", {})
        for path, methods in paths.items():
            example_output[path] = {}

            # 新增：先提取 path-level 的 parameters
            path_level_parameters = methods.get("parameters", [])

            for method, method_obj in methods.items():
                method_lower = method.lower()
                if method_lower not in ["get", "post", "put", "delete", "patch", "options", "head"]:
                    continue
                result = {"parameters": [], "requestBody": [], "x-dependencies": []}

                # 处理 parameters
                all_parameters = path_level_parameters + method_obj.get("parameters", [])
                for param in all_parameters:
                    param_data = {
                        "name": param.get("name"),
                        "type": param.get("schema", {}).get("type", "unknown"),
                        "description": param.get("description", ""),
                        "required": param.get("required", False),
                    }
                    result["parameters"].append(param_data)

                # 处理 requestBody
                request_body = method_obj.get("requestBody", {})
                content = request_body.get("content", {})
                schema = None

                preferred_types = [
                    "application/json",
                    "application/x-www-form-urlencoded",
                    "multipart/form-data",
                    "application/xml",
                    "application/octet-stream",
                    "text/plain",
                    "*/*"
                ]

                # 优先匹配常见类型
                for media_type in preferred_types:
                    if media_type in content:
                        schema = content[media_type].get("schema")
                        break

                # 否则查找包含 +json 的类型
                if not schema:
                    for media_type, media_content in content.items():
                        if "+json" in media_type or media_type.startswith("application/json"):
                            schema = media_content.get("schema")
                            break

                if schema:
                    result["requestBody"] = self.extract_schema_fields(schema)

                example_output[path][method_lower] = result

        return example_output

    def extract_schema_fields(self, schema, prefix="", required_fields=None):
        """
        递归提取 schema 字段，支持 object 和 array 类型。
        """
        fields = []
        required_fields = required_fields or schema.get("required", [])

        schema_type = schema.get("type", "string")
        if schema_type == "object":
            for prop, prop_schema in schema.get("properties", {}).items():
                full_name = f"{prefix}.{prop}" if prefix else prop
                # fields.extend(self.extract_schema_fields(
                #     prop_schema,
                #     prefix=full_name,
                #     required_fields=prop_schema.get("required", [])
                # ))
                fields.extend(self.extract_schema_fields(
                    prop_schema,
                    prefix=full_name,
                    required_fields=required_fields
                ))
        elif schema_type == "array":
            items_schema = schema.get("items", {})
            array_prefix = f"{prefix}[]" if prefix else "[]"
            fields.extend(self.extract_schema_fields(items_schema, prefix=array_prefix))
        else:
            fields.append({
                "name": prefix,
                "type": schema_type,
                "description": schema.get("description", ""),
                "required": prefix.split(".")[-1] in required_fields
            })

        return fields
