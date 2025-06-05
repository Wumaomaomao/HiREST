import logging, logging.config, argparse
from datetime import datetime
from pathlib import Path

from hirest.fuzzer.case_manager import CaseManager
from hirest.fuzzer.input_space_manager import InputSpaceManager
from hirest.fuzzer.fuzzer import Fuzzer
from hirest.fuzzer.mutator.operator.SISPmutator import SISPMutator
from hirest.fuzzer.mutator.operator.MISPSSmutator import MISPSSMutator
from hirest.fuzzer.mutator.operator.MISPmutator import MISPMutator
from hirest.fuzzer.mutator.controller.hierarchical_controller import HierarchicalMutationController
from hirest.fuzzer.renderer.renderer import Renderer
from hirest.fuzzer.executor.executor import Executor
from hirest.fuzzer.resp_checker.resp_checker import RespChecker

from hirest.utils.load_file import load_file

class JsonFileHandler(logging.FileHandler):
    """Custom file handler to write logs as a JSON array."""

    def emit(self, record):
        log_entry = self.format(record)
        log_entry = json.loads(log_entry)
        try:
            with open(self.baseFilename, "a", encoding="utf-8") as f:
                json.dump(json.loads(log_entry), f, indent=4) 
                f.write("\n")  
        except Exception:
            self.handleError(record)

class SimpleJsonFormatter(logging.Formatter):
    """Custom JSON formatter for HiREST.fuzzer.response_checker."""

    def format(self, record):
        log_record = record.getMessage()
        return json.dumps(log_record, indent=4)

def config_logging(service_name: str):
    service_name = service_name.lower()
    date = datetime.now().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%H%M%S")

    log_dir = Path(f"apis/{service_name}/log/{date}")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_filepath = log_dir / f"{service_name}_log_{date}_{time}.log"

    exec_log_dir = Path(f"apis/{service_name}/exec_log/{date}")
    exec_log_dir.mkdir(parents=True, exist_ok=True)
    exec_log_filepath = exec_log_dir / f"{service_name}_exec_log_{date}_{time}.log"

    result_dir = Path(f"apis/{service_name}/result/{date}")
    result_dir.mkdir(parents=True, exist_ok=True)
    result_filepath = result_dir / f"{service_name}_result_{date}_{time}.json"

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            },
            "exec_formatter": {
                "format": "%(asctime)s : %(message)s"
            },
            "simple_json_formatter": {
                "()": SimpleJsonFormatter,  
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
            "exec_file": {
                "class": "logging.FileHandler",
                "filename": exec_log_filepath,
                "formatter": "exec_formatter",
                "level": "DEBUG",
            },
            "result_file": {
                "()": JsonFileHandler,
                "filename": result_filepath,
                "formatter": "simple_json_formatter", 
                "level": "DEBUG",
            },
        },
        "loggers": {
            "hirest": {
                "level": "DEBUG",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "hirest.fuzzer.executor": {
                "level": "DEBUG",
                "handlers": ["exec_file"],
                "propagate": False,
            },
            "hirest.fuzzer.resp_checker": {
                "level": "DEBUG",
                "handlers": ["result_file"],  # 输出到 result_file
                "propagate": False,
            },
        }
    }

    logging.config.dictConfig(LOGGING_CONFIG)


SERVICE = {
    "languagetool": {
        "base_url": "http://localhost:49981/v2/"
    },
    "ncs": {
        "base_url": "http://localhost:50102/"
    },
    "person": {
        "base_url": "http://localhost:50111/"
    },
    "restcountries": {
        "base_url": "http://localhost:50106/rest/"
    },
    "scs":{
        "base_url": "http://localhost:50108/"
    },
    "news":{
        "base_url": "http://localhost:50103/"
    },
    "youtube":{
        "base_url": "http://localhost:9009/api/"
    }
}

base_path = "/root/ase/HiREST"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fuzzing REST APIs')
    parser.add_argument('--service', type=str, required=True, help='Name of the service to fuzz')
    parser.add_argument('--time_limit', type=int, default=3600, help='Time limit for fuzzing (seconds)')
    parser.add_argument('--requests', type=int, default=1000, help='Maximum number of requests')
    args = parser.parse_args()

    def fuzzing_service(service_name: str, max_requests: int, time_limit: int):
        base_url = SERVICE[service_name]["base_url"]
        config_logging(service_name)
        logger = logging.getLogger(__name__)

        input_space_manager = InputSpaceManager()
        misp_data = load_file(f"{base_path}/apis/{service_name}/partition/misp.json")
        input_space_manager.load_misps(misp_data)
        sisp_data = load_file(f"{base_path}/apis/{service_name}/partition/sisp.json")
        input_space_manager.load_sisps(sisp_data)

        case_manager = CaseManager(input_space_manager)
        op_data = load_file(f"{base_path}/apis/{service_name}/op_slide/operation_template.json")
        case_manager.load_operations(op_data)
        seed_data = load_file(f"{base_path}/apis/{service_name}/seed/seed.json")
        case_manager.load_seeds(seed_data)

        sisp_mutator = SISPMutator()
        mispss_mutator = MISPSSMutator()
        misp_mutator = MISPMutator()
        mutation_controller = HierarchicalMutationController(
            input_space_manager=input_space_manager,
            mutators=[sisp_mutator, mispss_mutator, misp_mutator],
        )
        renderer = Renderer(base_url=base_url)
        executor = Executor()
        response_checker = RespChecker()

        fuzzer = Fuzzer(
            input_space_manager=input_space_manager,
            case_manager=case_manager,
            mutation_controller=mutation_controller,
            renderer=renderer,
            executor=executor,
            response_checker=response_checker,
            max_requests=max_requests,
            time_limit=time_limit,
        )

        fuzzer.start()

    fuzzing_service(args.service, args.requests, args.time_limit)

