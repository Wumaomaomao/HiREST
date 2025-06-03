import argparse
import json
import os
import sys
from pathlib import Path
import time
import threading
import signal
from unittest import result

from hirest.generator.partition.misp.misp_gen import MISPGenerator
from hirest.generator.partition.sisp.sisp_gen import SISPGenerator
from hirest.generator.seed.seed import Seed
from hirest.parser.openapi import OpenAPIParser
from hirest.parser.preparser.check import Check


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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run hirest's offline pipeline")
    parser.add_argument('-i','--input_path', type=str, required=True, help="Path to OpenAPI spec")
    parser.add_argument('-s','--seed_size', type=int, required=False, help="Number of seeds to generate")

    args = parser.parse_args()
    service_root = Path(args.input_path).parents[1]
    service_name = service_root.name
    output_path = f"./apis/{service_name}/op_slide/operation_template.json"
    SISP_output_path = f"./apis/{service_name}/partition/sisp.json"
    MISP_output_path = f"./apis/{service_name}/partition/misp.json"
    seed_output_path = f"./apis/{service_name}/seed/seed.json"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(SISP_output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(MISP_output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(seed_output_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"\033[33m[YELLOW represents the program is running]\033[0m")
    print(f"\033[34m[BLUE represents the terminal information printed by the program]\033[0m")
    print(f"\033[32m[GREEN represents successful execution of the program]\033[0m")
    print(f"\033[31m[RED represents abnormal termination of the program]\033[0m")

    print("-------------MAIN--------------")

    print(f"\033[33mVerification before offline...\033[0m")
    check_file = Check(args.input_path)
    print(f"\033[32mSuccessfully completed verification!\033[0m")

    # parse
    stop_event = log_time("Parsing OpenAPI and saving operation information")
    swagger_parse_data = OpenAPIParser(args.input_path)
    swagger_parse_data.save_op_slides(output_path)
    stop_event.set()
    time.sleep(2)

    # generate SISP
    stop_event = log_time("Generating and saving SISP")
    SISP_data = SISPGenerator(
        operation_data_path=output_path,
        llm_und_data=swagger_parse_data.llm_for_sisp_swagger_understanding
    )
    SISP_data.save_list_SISP(SISP_output_path)
    stop_event.set()
    time.sleep(2)

    # generate mixed MISP
    stop_event = log_time("Generating and saving MISP")
    MISP_data = MISPGenerator(
        swagger_llm_extract_dep=swagger_parse_data.llm_dependencies,
        operation_data_path=output_path,
        single_space_data=SISP_data.sisp_pre_data
    )
    MISP_data.save_List_MISP(MISP_output_path)
    stop_event.set()
    time.sleep(2)

    # generate seeds
    user_give_seed_size = 100 # default value is between 2 and 10
    stop_event = log_time("Generating and saving Seeds")
    seed_data = Seed(
        mixed_space_data=MISP_data.mixed_space_partition_data,
        size=user_give_seed_size
    )
    seed_data.save_seeds(seed_output_path)
    stop_event.set()
    time.sleep(2)