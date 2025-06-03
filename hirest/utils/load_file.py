import json
import yaml

def load_file(file_path: str):
    """
    Load a JSON or YAML file based on the file extension.

    Parameters
    ----------
    file_path : str
        The path to the file to be loaded.

    Returns
    -------
    dict
        The content of the file as a dictionary.

    Raises
    ------
    ValueError
        If the file extension is not supported.
    FileNotFoundError
        If the file does not exist.
    """
    try:
        if file_path.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif file_path.endswith(('.yaml', '.yml')):
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            raise ValueError("Unsupported file format. Only .json, .yaml, and .yml are supported.")
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to load file {file_path}: {e}")