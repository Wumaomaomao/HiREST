import json
import os

import yaml


def load_data(file_path: str):
    with open(file_path, 'r', encoding="utf-8") as f:
        if file_path.endswith(".json"):
            return json.load(f)
        else:
            return yaml.safe_load(f)

def write_data(file_path: str, data):
    output_dir = os.path.dirname(file_path)
    os.makedirs(output_dir, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)