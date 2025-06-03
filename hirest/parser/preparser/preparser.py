import json

import yaml


"""
4.18 update ok to generate no ref file.
"""


class PreParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_data = self.load_spec()
        self.parsed_ref_data = self.resolve_all_refs(self.file_data)

    def load_spec(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            if self.file_path.endswith(".json"):
                return json.load(f)
            else:
                return yaml.safe_load(f)

    def resolve_all_refs(self, obj, root=None, ref_cache=None):
        if root is None:
            root = obj
        if ref_cache is None:
            ref_cache = {}

        if isinstance(obj, dict):
            if "$ref" in obj:
                ref_path = obj["$ref"]
                if ref_path in ref_cache:
                    return ref_cache[ref_path]
                ref_parts = ref_path.lstrip("#/").split("/")
                ref_obj = root
                for part in ref_parts:
                    ref_obj = ref_obj.get(part, {})
                resolved = self.resolve_all_refs(ref_obj, root, ref_cache)
                ref_cache[ref_path] = resolved
                return resolved
            else:
                return {k: self.resolve_all_refs(v, root, ref_cache) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.resolve_all_refs(item, root, ref_cache) for item in obj]
        else:
            return obj

