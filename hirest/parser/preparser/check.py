from pathlib import Path
import json
import yaml


def validate(file_path: str) -> None:

    # 检查文件是否存在
    if not Path(file_path).exists():
        raise Exception(f"\033[31mthe file path {file_path} does not exist !\033[0m")

    # 检查文件是否是.json/.yaml/.yml
    if not (file_path.endswith(".json") or file_path.endswith((".yaml", ".yml"))):
        raise Exception(f"\033[31mUnsupported file format. Please use JSON or YAML !\033[0m")

    # 尝试解析 JSON 或 YAML
    try:
        with open(file_path, "r") as f:
            if file_path.endswith(".json"):
                spec = json.load(f)
            else:
                spec = yaml.safe_load(f)
    except Exception as e:
        raise Exception(f"\033[31m❌ Failed to parse JSON/YAML file: {e}\033[0m")

    # 检查 openapi 或 swagger 版本
    if "swagger" in spec:
        if not spec["swagger"].startswith("2.0"):
            raise Exception(f"\033[31mUnsupported Swagger version: {spec['swagger']}\033[0m")
    elif "openapi" in spec:
        if not spec["openapi"].startswith("3."):
            raise Exception(f"\033[31mUnsupported OpenAPI version: {spec['openapi']}\033[0m")
    else:
        raise Exception("\033[31m❌ No swagger/openapi version field found!\033[0m")

    # 检查 paths 下 methods 是否为 dict
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            raise Exception(f"\033[31m❌ Path '{path}' methods should be a dict!\033[0m")
        for method, operation in methods.items():
            if method.lower() in ["get", "post", "put", "delete", "patch", "head", "options"]:
                if not isinstance(operation, dict):
                    raise Exception(f"\033[31m❌ Method '{method}' in path '{path}' should be a dict!\033[0m")

    # 检查 $ref 是否存在且无循环
    visited_refs = set()
    def resolve_ref(ref, root):
        if not ref.startswith("#/"):
            raise Exception(f"\033[31m❌ External references are not supported: {ref}\033[0m")
        parts = ref.lstrip("#/").split("/")
        target = root
        for part in parts:
            if part not in target:
                raise Exception(f"\033[31m❌ $ref target '{ref}' does not exist in the document!\033[0m")
            target = target[part]
        return target
    def traverse(obj, root, history):
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref = obj["$ref"]
                if ref in history:
                    raise Exception(f"\033[31m❌ Circular $ref detected: {ref}\033[0m")
                history.add(ref)
                target = resolve_ref(ref, root)
                traverse(target, root, history)
                history.remove(ref)
            for v in obj.values():
                traverse(v, root, history)
        elif isinstance(obj, list):
            for item in obj:
                traverse(item, root, history)
    traverse(spec, spec, set())


class Check:
    def __init__(self, file_path: str):
        self.file_path = file_path
        validate(self.file_path)