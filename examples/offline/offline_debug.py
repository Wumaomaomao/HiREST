import argparse
from datetime import datetime
import json
import os
import sys
from pathlib import Path
import time
import threading
import signal
from unittest import result
import logging
import logging.config
from typing import Any, Dict, List, Optional, Set

from hirest.generator.partition.misp.misp_gen import MISPGenerator
from hirest.generator.partition.misp.llm_gen.mixed_space_partition import mixed_space_partition_gen
from hirest.generator.partition.misp.llm_gen.multi_space_partition import multi_space_partition_gen
from hirest.generator.partition.sisp.sisp_gen import SISPGenerator
from hirest.generator.partition.sisp.llm_gen.single_space_partition import single_space_partition_gen_every
from hirest.generator.seed.seed import Seed
from hirest.parser.openapi import OpenAPIParser
from hirest.parser.preparser.check import Check


def build_dep_from_op_slides(op_slides: list) -> dict:
    dep_dict = {}
    for item in op_slides:
        path = item.get("url") or item.get("raw_doc_slide", {}).get("path")
        method = (item.get("method") or item.get("raw_doc_slide", {}).get("method", "")).lower()
        if not path or not method:
            continue
        dep_dict.setdefault(path, {})[method] = {
            "all-dependencies": item.get("dependencies", [])
        }
    return dep_dict


def load_json_if_exists(file_path: str) -> Optional[Any]:
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(file_path: str, data: Any):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def build_input_fingerprint(input_path: str) -> Dict[str, Any]:
    stat = os.stat(input_path)
    return {
        "path": str(Path(input_path).resolve()),
        "size": stat.st_size,
        "mtime": stat.st_mtime,
    }


def init_checkpoint(service_name: str, input_path: str) -> Dict[str, Any]:
    return {
        "version": 1,
        "service_name": service_name,
        "input_fingerprint": build_input_fingerprint(input_path),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "stages": {},
    }


def load_checkpoint(
    checkpoint_path: str,
    service_name: str,
    input_path: str,
    allow_resume: bool,
    reset_checkpoint: bool,
) -> Dict[str, Any]:
    if reset_checkpoint and os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)

    if not os.path.exists(checkpoint_path):
        checkpoint = init_checkpoint(service_name, input_path)
        save_json(checkpoint_path, checkpoint)
        return checkpoint

    checkpoint = load_json_if_exists(checkpoint_path)
    if not isinstance(checkpoint, dict):
        checkpoint = init_checkpoint(service_name, input_path)
        save_json(checkpoint_path, checkpoint)
        return checkpoint

    if not allow_resume:
        checkpoint = init_checkpoint(service_name, input_path)
        save_json(checkpoint_path, checkpoint)
        return checkpoint

    input_fingerprint = build_input_fingerprint(input_path)
    if checkpoint.get("input_fingerprint") != input_fingerprint:
        print("\033[33m[offline][INFO] OpenAPI input changed, restarting pipeline from scratch.\033[0m")
        checkpoint = init_checkpoint(service_name, input_path)
        save_json(checkpoint_path, checkpoint)
        return checkpoint

    checkpoint.setdefault("stages", {})
    checkpoint["updated_at"] = datetime.now().isoformat()
    save_json(checkpoint_path, checkpoint)
    return checkpoint


def mark_stage_completed(
    checkpoint_path: str,
    checkpoint: Dict[str, Any],
    stage_name: str,
    extra: Optional[Dict[str, Any]] = None,
):
    stage_data = {
        "status": "completed",
        "completed_at": datetime.now().isoformat(),
    }
    if extra:
        stage_data.update(extra)

    checkpoint.setdefault("stages", {})[stage_name] = stage_data
    checkpoint["updated_at"] = datetime.now().isoformat()
    save_json(checkpoint_path, checkpoint)


def is_stage_completed(
    checkpoint: Dict[str, Any], stage_name: str, required_files: Optional[list] = None
) -> bool:
    stage = checkpoint.get("stages", {}).get(stage_name, {})
    if stage.get("status") != "completed":
        return False
    if required_files:
        return all(os.path.exists(path) for path in required_files)
    return True


def api_key_of(method: str, path: str) -> str:
    return f"{method.lower()} {path}"


def get_stage_completed_apis(checkpoint: Dict[str, Any], stage_name: str) -> Set[str]:
    stage = checkpoint.get("stages", {}).get(stage_name, {})
    completed = stage.get("completed_apis", [])
    return set(completed if isinstance(completed, list) else [])


def mark_stage_api_completed(
    checkpoint_path: str,
    checkpoint: Dict[str, Any],
    stage_name: str,
    api_key: str,
    extra: Optional[Dict[str, Any]] = None,
):
    stage = checkpoint.setdefault("stages", {}).setdefault(stage_name, {})
    stage["status"] = "in_progress"
    completed_apis = set(stage.get("completed_apis", []))
    completed_apis.add(api_key)
    stage["completed_apis"] = sorted(completed_apis)
    stage["updated_at"] = datetime.now().isoformat()
    if extra:
        stage.update(extra)
    checkpoint["updated_at"] = datetime.now().isoformat()
    save_json(checkpoint_path, checkpoint)


def extract_sisp_api_keys(sisp_pre_data: list) -> Set[str]:
    keys: Set[str] = set()
    for item in sisp_pre_data:
        method = item.get("http_verb")
        path = item.get("url_path")
        if method and path:
            keys.add(api_key_of(method, path))
    return keys


def extract_partition_api_keys(partition_data: dict) -> Set[str]:
    keys: Set[str] = set()
    if not isinstance(partition_data, dict):
        return keys
    for path, methods in partition_data.items():
        if not isinstance(methods, dict):
            continue
        for method in methods.keys():
            keys.add(api_key_of(method, path))
    return keys


def build_sisp_pre_data_from_saved_sisp(saved_sisp: list) -> list:
    sisp_pre_data = []
    for item in saved_sisp:
        op_name = item.get("op_name", "")
        if " " not in op_name:
            continue
        http_verb, url_path = op_name.split(" ", 1)
        valid_items = [
            {
                "input_space_category": valid.get("category"),
                "description": valid.get("description"),
                "representative_samples": valid.get("samples", []),
            }
            for valid in item.get("valid", [])
        ]
        invalid_items = [
            {
                "input_space_category": invalid.get("category"),
                "description": invalid.get("description"),
                "representative_samples": invalid.get("samples", []),
            }
            for invalid in item.get("invalid", [])
        ]
        sisp_pre_data.append(
            {
                "http_verb": http_verb,
                "url_path": url_path,
                "parameter_name": item.get("param_name"),
                "type": item.get("type"),
                "format": item.get("format"),
                "valid_input_space_categories": valid_items,
                "invalid_input_space_categories": invalid_items,
            }
        )
    return sisp_pre_data


def _is_miss_key(category_item: dict) -> bool:
    return (category_item.get("input_space_category") or "") == "<MISS_KEY>"


def _infer_required_from_sisp_param(param_item: dict) -> bool:
    valid_items = param_item.get("valid_input_space_categories", []) or []
    invalid_items = param_item.get("invalid_input_space_categories", []) or []
    has_miss_in_valid = any(_is_miss_key(item) for item in valid_items if isinstance(item, dict))
    has_miss_in_invalid = any(_is_miss_key(item) for item in invalid_items if isinstance(item, dict))

    if has_miss_in_invalid and not has_miss_in_valid:
        return True
    if has_miss_in_valid and not has_miss_in_invalid:
        return False
    if has_miss_in_invalid and has_miss_in_valid:
        return True
    return False


def _pick_single_format(param_item: dict):
    fmt = param_item.get("format")
    if isinstance(fmt, list):
        return fmt[0] if len(fmt) == 1 else None
    if isinstance(fmt, str):
        return fmt
    return None


def _to_mixed_single_space(param_item: dict, category_item: dict, tag: str = "valid") -> dict:
    samples = category_item.get("representative_samples", [])
    if not isinstance(samples, list):
        samples = [samples]

    return {
        "tag": tag,
        "type": param_item.get("type"),
        "format": _pick_single_format(param_item),
        "input_space_category": category_item.get("input_space_category", "<UNNAMED_SPACE>"),
        "description": category_item.get("description", ""),
        "representative_samples": samples,
    }


def _present_valid_spaces(param_item: dict) -> list:
    valid_items = [
        item
        for item in (param_item.get("valid_input_space_categories", []) or [])
        if isinstance(item, dict)
    ]
    non_miss = [item for item in valid_items if not _is_miss_key(item)]
    chosen = non_miss if non_miss else valid_items

    if not chosen:
        chosen = [
            {
                "input_space_category": "<FALLBACK_VALID>",
                "description": "Fallback valid space generated by no_misp mode.",
                "representative_samples": [None],
            }
        ]

    return [_to_mixed_single_space(param_item, item, tag="valid") for item in chosen]


def _miss_key_space(param_item: dict) -> dict:
    valid_items = [
        item
        for item in (param_item.get("valid_input_space_categories", []) or [])
        if isinstance(item, dict)
    ]
    invalid_items = [
        item
        for item in (param_item.get("invalid_input_space_categories", []) or [])
        if isinstance(item, dict)
    ]

    for item in valid_items:
        if _is_miss_key(item):
            return _to_mixed_single_space(param_item, item, tag="valid")
    for item in invalid_items:
        if _is_miss_key(item):
            return _to_mixed_single_space(param_item, item, tag="valid")

    fallback = {
        "input_space_category": "<MISS_KEY>",
        "description": "Parameter omitted in this scalable space.",
        "representative_samples": [None],
    }
    return _to_mixed_single_space(param_item, fallback, tag="valid")


def build_no_misp_mixed_space_data(sisp_pre_data: list) -> dict:
    grouped: Dict[tuple, Dict[str, dict]] = {}

    for item in sisp_pre_data:
        path = item.get("url_path")
        method = (item.get("http_verb") or "").lower()
        param_name = item.get("parameter_name")
        if not path or not method or not param_name:
            continue
        grouped.setdefault((path, method), {})
        if param_name not in grouped[(path, method)]:
            grouped[(path, method)][param_name] = item

    mixed_space_data: dict = {}

    for (path, method), params in grouped.items():
        required_params: List[str] = []
        optional_params: List[str] = []
        for param_name, param_item in params.items():
            if _infer_required_from_sisp_param(param_item):
                required_params.append(param_name)
            else:
                optional_params.append(param_name)

        api_spaces: dict = {
            "space1": {
                "satisfied-dependencies": "Minimum input space.",
                "involved-parameters": required_params,
                "subspace1": {
                    "single-parameter-spaces": {
                        param_name: _present_valid_spaces(params[param_name])
                        for param_name in required_params
                    },
                    "parameter": required_params,
                    "parameter-value": [],
                    "parameter-parameter": [],
                },
            }
        }

        next_idx = 2
        for param_name in optional_params:
            api_spaces[f"space{next_idx}"] = {
                "satisfied-dependencies": f"Scalable space for optional parameter '{param_name}'.",
                "involved-parameters": [param_name],
                "subspace1": {
                    "single-parameter-spaces": {
                        param_name: _present_valid_spaces(params[param_name])
                    },
                    "parameter": [param_name],
                    "parameter-value": [],
                    "parameter-parameter": [],
                },
                "subspace2": {
                    "single-parameter-spaces": {
                        param_name: [_miss_key_space(params[param_name])]
                    },
                    "parameter": [],
                    "parameter-value": [],
                    "parameter-parameter": [],
                },
            }
            next_idx += 1

        mixed_space_data.setdefault(path, {})
        mixed_space_data[path][method] = api_spaces

    return mixed_space_data


def build_mixed_space_data_from_saved_misp(saved_misp: list) -> dict:
    mixed_space_data = {}
    for item in saved_misp:
        op_name = item.get("op_name", "")
        if " " not in op_name:
            continue
        method, path = op_name.split(" ", 1)
        method = method.lower()
        mixed_space_data.setdefault(path, {})
        mixed_space_data[path].setdefault(method, {})

        for space in item.get("space_list", []):
            space_name = space.get("space_name")
            if not space_name:
                continue
            mixed_space_data[path][method].setdefault(space_name, {})
            space_content = mixed_space_data[path][method][space_name]
            space_content["satisfied-dependencies"] = space.get(
                "satisfied_dependencies", ""
            )
            space_content["involved-parameters"] = space.get("involved_parameters", [])

            for subspace in space.get("subspace_list", []):
                subspace_name = subspace.get("subspace_name")
                if not subspace_name:
                    continue
                space_content[subspace_name] = {
                    "single-parameter-spaces": subspace.get(
                        "single_parameter_spaces", {}
                    ),
                    "parameter": subspace.get("parameter", []),
                    "parameter-value": subspace.get("parameter_value", []),
                    "parameter-parameter": subspace.get("parameter_parameter", []),
                }
    return mixed_space_data


def load_mixed_space_data(partition_path: str) -> dict:
    with open(partition_path, "r", encoding="utf-8") as f:
        partition_data = json.load(f)

    if isinstance(partition_data, dict):
        return partition_data
    if isinstance(partition_data, list):
        return build_mixed_space_data_from_saved_misp(partition_data)

    raise ValueError(
        f"Unsupported partition file format in {partition_path}: {type(partition_data)}"
    )


def log_time(tag: str):
    start_time = time.time()
    stop_event = threading.Event()
    loading_symbols = ["", ".", "..", "...", "⏳"]

    def run_timer():
        try:
            idx = 0
            print(f"\r\033[33m[offline][INFO][{tag}] running for {0.000:.3f} seconds{' ' * 10}\033[0m", end='', flush=True)
            while not stop_event.is_set():
                elapsed = time.time() - start_time
                symbol = loading_symbols[idx % len(loading_symbols)]
                print(f"\r\033[33m[offline][INFO][{tag}] running for {elapsed:.3f} seconds {symbol}{' ' * 10}\033[0m", end='', flush=True)
                idx += 1
                time.sleep(0.4)
        except KeyboardInterrupt:
            stop_event.set()
        finally:
            print(f"\r\033[32m[offline][INFO][{tag}] took {time.time() - start_time:.3f} seconds.{' ' * 20}\033[0m")

    thread = threading.Thread(target=run_timer)
    thread.daemon = True
    thread.start()

    def handle_sigint(signum, frame):
        stop_event.set()
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, handle_sigint)

    return stop_event


def config_logging(service_name: str):
    service_name = service_name.lower()
    date = datetime.now().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%H%M%S")

    log_dir = Path(f"apis/{service_name}/log/offline/{date}")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_filepath = log_dir / f"{service_name}_offline_log_{date}_{time}.log"

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "WARNING",
            },
            "file": {
                "class": "logging.FileHandler",
                "filename": log_filepath,
                "formatter": "default",
                "level": "DEBUG",
            },
        },
        "loggers": {
            "hirest": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(LOGGING_CONFIG)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run hirest's offline pipeline")
    parser.add_argument('-i','--input_path', type=str, required=True, help="Path to OpenAPI spec")
    parser.add_argument('-s','--seed_size', type=int, required=False, help="Number of seeds to generate")
    parser.add_argument('--misp_from_files', action='store_true', help="Reuse op_slide and sisp files to run only MISP")
    parser.add_argument('--seed_only', action='store_true', help="Only generate seeds from a partition file")
    parser.add_argument('--partition_path', type=str, required=False, help="Path to partition file used by --seed_only (mixed-space json or misp.json)")
    parser.add_argument('--checkpoint_path', type=str, required=False, help="Path to checkpoint file (default: ./apis/<service>/result/offline_checkpoint.json)")
    parser.add_argument('--no_resume', action='store_true', help="Ignore previous checkpoint and rerun all stages")
    parser.add_argument('--reset_checkpoint', action='store_true', help="Delete existing checkpoint before running")
    parser.add_argument(
        '--no_misp',
        action='store_true',
        help="Generate MISP from existing sisp.json without any LLM (required->space1, optional->scalable spaces).",
    )
    parser.add_argument(
        '--ablation_no_constraints',
        action='store_true',
        help="Ablation mode: skip single/multi constraint extraction and use raw OpenAPI docs as partition input.",
    )

    

    args = parser.parse_args()
    service_root = Path(args.input_path).parents[1]
    service_name = service_root.name
    output_path = f"./apis/{service_name}/op_slide/operation_template.json"
    SISP_output_path = f"./apis/{service_name}/partition/sisp.json"
    MISP_output_path = f"./apis/{service_name}/partition/misp.json"
    seed_output_path = f"./apis/{service_name}/seed/seed.json"
    result_dir = Path(f"./apis/{service_name}/result")
    checkpoint_path = args.checkpoint_path or str(result_dir / "offline_checkpoint.json")
    parse_llm_und_path = str(result_dir / "parse_llm_und.json")
    parse_dep_path = str(result_dir / "parse_dep.json")
    misp_multi_partial_path = str(result_dir / "misp_multi_partial.json")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(SISP_output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(MISP_output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(seed_output_path).parent.mkdir(parents=True, exist_ok=True)
    result_dir.mkdir(parents=True, exist_ok=True)

    checkpoint = load_checkpoint(
        checkpoint_path=checkpoint_path,
        service_name=service_name,
        input_path=args.input_path,
        allow_resume=not args.no_resume,
        reset_checkpoint=args.reset_checkpoint,
    )

    print(f"\033[33m[YELLOW represents the program is running]\033[0m")
    print(f"\033[34m[BLUE represents the terminal information printed by the program]\033[0m")
    print(f"\033[32m[GREEN represents successful execution of the program]\033[0m")
    print(f"\033[31m[RED represents abnormal termination of the program]\033[0m")

    print("-------------MAIN--------------")

    print(f"\033[33mVerification before offline...\033[0m")
    check_file = Check(args.input_path)
    mark_stage_completed(checkpoint_path, checkpoint, "verify")
    print(f"\033[32mSuccessfully completed verification!\033[0m")

    if args.seed_only:
        user_give_seed_size = args.seed_size if args.seed_size is not None else 10
        partition_path = args.partition_path or MISP_output_path

        if not os.path.exists(partition_path):
            raise FileNotFoundError(
                f"partition file not found: {partition_path}. "
                f"Use --partition_path to specify an existing file."
            )

        stop_event = log_time("Generating and saving Seeds from partition file")
        mixed_space_data = load_mixed_space_data(partition_path)
        seed_data = Seed(mixed_space_data=mixed_space_data, size=user_give_seed_size)
        seed_data.save_seeds(seed_output_path)
        mark_stage_completed(
            checkpoint_path,
            checkpoint,
            "seed",
            {
                "seed_size": user_give_seed_size,
                "seed_output_path": seed_output_path,
                "partition_path": partition_path,
            },
        )
        stop_event.set()
        time.sleep(2)
        print(
            f"\033[32mSeeds generated from partition file: {partition_path} -> {seed_output_path}\033[0m"
        )
        sys.exit(0)

    if args.no_misp:
        saved_sisp = load_json_if_exists(SISP_output_path)
        if not isinstance(saved_sisp, list):
            raise FileNotFoundError(
                f"sisp file not found or invalid: {SISP_output_path}. "
                "Please generate sisp first."
            )

        stop_event = log_time("Generating and saving MISP (no_misp mode)")
        sisp_pre_data = build_sisp_pre_data_from_saved_sisp(saved_sisp)
        mixed_space_data = build_no_misp_mixed_space_data(sisp_pre_data)

        misp_saver = MISPGenerator(
            swagger_llm_extract_dep={},
            operation_data_path=output_path,
            single_space_data=sisp_pre_data,
        )
        misp_saver.mixed_space_partition_data = mixed_space_data
        misp_saver.save_List_MISP(MISP_output_path)

        mark_stage_completed(
            checkpoint_path,
            checkpoint,
            "misp",
            {
                "misp_output_path": MISP_output_path,
                "source": "no_misp",
                "api_count": len(extract_partition_api_keys(mixed_space_data)),
            },
        )
        stop_event.set()
        time.sleep(2)

        user_give_seed_size = args.seed_size if args.seed_size is not None else 10
        stop_event = log_time("Generating and saving Seeds (no_misp mode)")
        seed_data = Seed(
            mixed_space_data=mixed_space_data,
            size=user_give_seed_size,
        )
        seed_data.save_seeds(seed_output_path)
        mark_stage_completed(
            checkpoint_path,
            checkpoint,
            "seed",
            {
                "seed_size": user_give_seed_size,
                "seed_output_path": seed_output_path,
                "source": "no_misp",
            },
        )
        stop_event.set()
        time.sleep(2)
        print(f"\033[32mMISP/Seeds generated by no_misp mode: {MISP_output_path}, {seed_output_path}\033[0m")
        sys.exit(0)

    if args.misp_from_files:
        stop_event = log_time("Generating and saving MISP from existing files")
        with open(output_path, "r", encoding="utf-8") as f:
            op_slides = json.load(f)
        with open(SISP_output_path, "r", encoding="utf-8") as f:
            saved_sisp = json.load(f)

        dep_data = build_dep_from_op_slides(op_slides)
        sisp_pre_data = build_sisp_pre_data_from_saved_sisp(saved_sisp)

        MISP_data = MISPGenerator(
            swagger_llm_extract_dep=dep_data,
            operation_data_path=output_path,
            single_space_data=sisp_pre_data
        )
        MISP_data.save_List_MISP(MISP_output_path)
        mark_stage_completed(
            checkpoint_path,
            checkpoint,
            "misp",
            {
                "misp_output_path": MISP_output_path,
                "source": "misp_from_files",
            },
        )
        stop_event.set()
        time.sleep(2)
        print(f"\033[32mMISP generated from existing files: {MISP_output_path}\033[0m")
        sys.exit(0)

    config_logging(service_name)
    logger = logging.getLogger(__name__)

    parse_completed = (not args.no_resume) and is_stage_completed(
        checkpoint, "parse", [output_path]
    )
    sisp_completed = (not args.no_resume) and is_stage_completed(
        checkpoint, "sisp", [SISP_output_path]
    )
    misp_completed = (not args.no_resume) and is_stage_completed(
        checkpoint, "misp", [MISP_output_path]
    )
    seed_completed = (not args.no_resume) and is_stage_completed(
        checkpoint, "seed", [seed_output_path]
    )

    if args.ablation_no_constraints:
        print("\033[33m[offline][INFO] Ablation mode enabled: skip constraint extraction and use raw doc for partition/mixed.\033[0m")
        parse_completed = False
        sisp_completed = False
        misp_completed = False
        seed_completed = False

    llm_und_data = None
    dep_data = None
    sisp_pre_data = None
    mixed_space_data = None

    # parse
    if parse_completed:
        print("\033[34m[offline][INFO] Skip parse stage (checkpoint hit).\033[0m")
        llm_und_data = load_json_if_exists(parse_llm_und_path)
        dep_data = load_json_if_exists(parse_dep_path)
    else:
        stop_event = log_time("Parsing OpenAPI and saving operation information")
        swagger_parse_data = OpenAPIParser(args.input_path)

        if args.ablation_no_constraints:
            # Ablation: skip both single-parameter and multi-parameter constraint extraction stages.
            llm_und_data = []
            dep_data = {}
        else:
            swagger_parse_data.extract_service_knowledge()
            swagger_parse_data.extract_parameter_constraints()
            swagger_parse_data.extract_api_dependencies()

        swagger_parse_data.gen_operation_slides()
        swagger_parse_data.save_op_slides(output_path)

        if not args.ablation_no_constraints:
            llm_und_data = swagger_parse_data.llm_for_sisp_swagger_understanding
            dep_data = swagger_parse_data.llm_dependencies
        save_json(parse_llm_und_path, llm_und_data)
        save_json(parse_dep_path, dep_data)
        mark_stage_completed(
            checkpoint_path,
            checkpoint,
            "parse",
            {
                "operation_output_path": output_path,
                "parse_llm_und_path": parse_llm_und_path,
                "parse_dep_path": parse_dep_path,
            },
        )

        stop_event.set()
        time.sleep(1)

    # generate SISP
    if sisp_completed:
        print("\033[34m[offline][INFO] Skip sisp stage (checkpoint hit).\033[0m")
        saved_sisp = load_json_if_exists(SISP_output_path) or []
        sisp_pre_data = build_sisp_pre_data_from_saved_sisp(saved_sisp)
    else:
        if llm_und_data is None:
            print("\033[33m[offline][INFO] Missing parse context for SISP, rerunning parse stage.\033[0m")
            stop_event = log_time("Parsing OpenAPI and saving operation information")
            swagger_parse_data = OpenAPIParser(args.input_path)
            if args.ablation_no_constraints:
                llm_und_data = []
                dep_data = {}
            else:
                swagger_parse_data.extract_service_knowledge()
                swagger_parse_data.extract_parameter_constraints()
                swagger_parse_data.extract_api_dependencies()
            swagger_parse_data.gen_operation_slides()
            swagger_parse_data.save_op_slides(output_path)
            if not args.ablation_no_constraints:
                llm_und_data = swagger_parse_data.llm_for_sisp_swagger_understanding
                dep_data = swagger_parse_data.llm_dependencies
            save_json(parse_llm_und_path, llm_und_data)
            save_json(parse_dep_path, dep_data)
            mark_stage_completed(
                checkpoint_path,
                checkpoint,
                "parse",
                {
                    "operation_output_path": output_path,
                    "parse_llm_und_path": parse_llm_und_path,
                    "parse_dep_path": parse_dep_path,
                },
            )
            stop_event.set()
            time.sleep(1)

        stop_event = log_time("Generating and saving SISP")
        checkpoint_sisp_done = get_stage_completed_apis(checkpoint, "sisp_api")
        saved_sisp = load_json_if_exists(SISP_output_path) or []
        saved_sisp_pre_data = build_sisp_pre_data_from_saved_sisp(saved_sisp)
        checkpoint_sisp_done |= extract_sisp_api_keys(saved_sisp_pre_data)

        sisp_saver = SISPGenerator(
            operation_data_path=output_path,
            llm_und_data=llm_und_data or [],
        )

        def on_sisp_api_done(api_key: str, _new_api_result: list, all_results: list):
            sisp_saver.sisp_pre_data = all_results
            sisp_saver.save_list_SISP(SISP_output_path)
            mark_stage_api_completed(
                checkpoint_path,
                checkpoint,
                "sisp_api",
                api_key,
                {
                    "sisp_output_path": SISP_output_path,
                },
            )

        sisp_pre_data = single_space_partition_gen_every(
            operation_data_path=output_path,
            llm_und_data=llm_und_data or [],
            use_raw_doc_input=args.ablation_no_constraints,
            completed_api_keys=checkpoint_sisp_done,
            existing_results=saved_sisp_pre_data,
            on_api_done=on_sisp_api_done,
        )

        sisp_saver.sisp_pre_data = sisp_pre_data
        sisp_saver.save_list_SISP(SISP_output_path)
        mark_stage_completed(
            checkpoint_path,
            checkpoint,
            "sisp",
            {
                "sisp_output_path": SISP_output_path,
                "api_count": len(extract_sisp_api_keys(sisp_pre_data)),
            },
        )
        stop_event.set()
        time.sleep(2)

    # generate mixed MISP
    if misp_completed:
        print("\033[34m[offline][INFO] Skip misp stage (checkpoint hit).\033[0m")
        mixed_space_data = load_mixed_space_data(MISP_output_path)
    else:
        if sisp_pre_data is None:
            saved_sisp = load_json_if_exists(SISP_output_path)
            if saved_sisp is None:
                raise RuntimeError("Cannot build MISP: sisp.json not found.")
            sisp_pre_data = build_sisp_pre_data_from_saved_sisp(saved_sisp)

        if dep_data is None:
            op_slides = load_json_if_exists(output_path)
            if op_slides is None:
                raise RuntimeError("Cannot build MISP: operation_template.json not found.")
            dep_data = build_dep_from_op_slides(op_slides)

        stop_event = log_time("Generating and saving MISP")
        checkpoint_misp_multi_done = get_stage_completed_apis(checkpoint, "misp_multi_api")
        checkpoint_misp_mixed_done = get_stage_completed_apis(checkpoint, "misp_mixed_api")

        existing_multi_space_data = load_json_if_exists(misp_multi_partial_path)
        if not isinstance(existing_multi_space_data, dict):
            existing_multi_space_data = {}

        existing_mixed_space_data = {}
        if os.path.exists(MISP_output_path):
            existing_mixed_space_data = load_mixed_space_data(MISP_output_path)
            checkpoint_misp_mixed_done |= extract_partition_api_keys(existing_mixed_space_data)

        def on_misp_multi_api_done(api_key: str, _new_api_result: dict, all_results: dict):
            save_json(misp_multi_partial_path, all_results)
            mark_stage_api_completed(
                checkpoint_path,
                checkpoint,
                "misp_multi_api",
                api_key,
                {
                    "misp_multi_partial_path": misp_multi_partial_path,
                },
            )

        multi_space_data = multi_space_partition_gen(
            dep=dep_data,
            op_data_path=output_path,
            use_raw_doc_input=args.ablation_no_constraints,
            completed_api_keys=checkpoint_misp_multi_done,
            existing_results=existing_multi_space_data,
            on_api_done=on_misp_multi_api_done,
        )
        save_json(misp_multi_partial_path, multi_space_data)

        misp_saver = MISPGenerator(
            swagger_llm_extract_dep=dep_data,
            operation_data_path=output_path,
            single_space_data=sisp_pre_data,
        )

        def on_misp_mixed_api_done(api_key: str, _new_api_result: dict, all_results: dict):
            misp_saver.mixed_space_partition_data = all_results
            misp_saver.save_List_MISP(MISP_output_path)
            mark_stage_api_completed(
                checkpoint_path,
                checkpoint,
                "misp_mixed_api",
                api_key,
                {
                    "misp_output_path": MISP_output_path,
                },
            )

        mixed_space_data = mixed_space_partition_gen(
            multi=multi_space_data,
            single_space_data=sisp_pre_data,
            completed_api_keys=checkpoint_misp_mixed_done,
            existing_results=existing_mixed_space_data,
            on_api_done=on_misp_mixed_api_done,
        )
        misp_saver.mixed_space_partition_data = mixed_space_data
        misp_saver.save_List_MISP(MISP_output_path)
        mark_stage_completed(
            checkpoint_path,
            checkpoint,
            "misp",
            {
                "misp_output_path": MISP_output_path,
                "misp_multi_partial_path": misp_multi_partial_path,
                "api_count": len(extract_partition_api_keys(mixed_space_data)),
            },
        )
        stop_event.set()
        time.sleep(2)

    # generate seeds
    user_give_seed_size = args.seed_size if args.seed_size is not None else 10
    if seed_completed:
        print("\033[34m[offline][INFO] Skip seed stage (checkpoint hit).\033[0m")
    else:
        if mixed_space_data is None:
            mixed_space_data = load_mixed_space_data(MISP_output_path)

        stop_event = log_time("Generating and saving Seeds")
        seed_data = Seed(
            mixed_space_data=mixed_space_data,
            size=user_give_seed_size,
        )
        seed_data.save_seeds(seed_output_path)
        mark_stage_completed(
            checkpoint_path,
            checkpoint,
            "seed",
            {
                "seed_size": user_give_seed_size,
                "seed_output_path": seed_output_path,
            },
        )
        stop_event.set()
        time.sleep(2)