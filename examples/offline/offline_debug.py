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
from typing import Any, Dict, Optional

from hirest.generator.partition.misp.misp_gen import MISPGenerator
from hirest.generator.partition.sisp.sisp_gen import SISPGenerator
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

        swagger_parse_data.extract_service_knowledge()
        swagger_parse_data.extract_parameter_constraints()
        swagger_parse_data.extract_api_dependencies()

        swagger_parse_data.gen_operation_slides()
        swagger_parse_data.save_op_slides(output_path)

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
            swagger_parse_data.extract_service_knowledge()
            swagger_parse_data.extract_parameter_constraints()
            swagger_parse_data.extract_api_dependencies()
            swagger_parse_data.gen_operation_slides()
            swagger_parse_data.save_op_slides(output_path)
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
        SISP_generator = SISPGenerator(
            operation_data_path=output_path,
            llm_und_data=llm_und_data,
        )
        SISP_generator.generate_sisp_from_constraints()
        SISP_generator.save_list_SISP(SISP_output_path)
        sisp_pre_data = SISP_generator.sisp_pre_data
        mark_stage_completed(
            checkpoint_path,
            checkpoint,
            "sisp",
            {
                "sisp_output_path": SISP_output_path,
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
        MISP_generator = MISPGenerator(
            swagger_llm_extract_dep=dep_data,
            operation_data_path=output_path,
            single_space_data=sisp_pre_data,
        )
        MISP_generator.generate_multi_space_partition()
        MISP_generator.generate_mixed_space_partition()
        MISP_generator.save_List_MISP(MISP_output_path)
        mixed_space_data = MISP_generator.mixed_space_partition_data
        mark_stage_completed(
            checkpoint_path,
            checkpoint,
            "misp",
            {
                "misp_output_path": MISP_output_path,
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