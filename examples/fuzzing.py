import json
import logging, logging.config, argparse
from datetime import datetime
from pathlib import Path
import subprocess

from hirest.fuzzer.case_manager import CaseManager
from hirest.fuzzer.input_space_manager import InputSpaceManager
from hirest.fuzzer.fuzzer import Fuzzer
from hirest.fuzzer.mutator.operator.SISPmutator import SISPMutator
from hirest.fuzzer.mutator.operator.MISPSSmutator import MISPSSMutator
from hirest.fuzzer.mutator.operator.MISPmutator import MISPMutator
from hirest.fuzzer.mutator.operator.perturbation_mutator import PerturbationMutator
from hirest.fuzzer.mutator.operator.wrongtype_mutator import WrongTypeMutator
from hirest.fuzzer.mutator.operator.missingrequired_mutator import MissingRequiredMutator
from hirest.fuzzer.mutator.controller.hierarchical_controller import HierarchicalMutationController
from hirest.fuzzer.mutator.controller.primitive_controller import PrimitiveMutationController
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


def keep_only_summary_in_result(result_filepath: str) -> None:
    result_path = Path(result_filepath)
    fallback_summary = {
        "status": "no_summary_generated",
        "reason": "No summary was generated during fuzzing; placeholder summary written by no-log mode.",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }

    if not result_path.exists():
        summary_payload = fallback_summary
    else:
        raw = result_path.read_text(encoding="utf-8").strip()
        if not raw:
            summary_payload = fallback_summary
        else:
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                summary_payload = fallback_summary
            else:
                if isinstance(payload, dict):
                    summary_payload = payload.get("summary", payload)
                else:
                    summary_payload = payload

                if summary_payload in (None, "", [], {}):
                    summary_payload = fallback_summary

    result_path.write_text(
        json.dumps(summary_payload, indent=4) + "\n",
        encoding="utf-8",
    )


def write_summary_result(result_filepath: str, summary: dict) -> None:
    result_path = Path(result_filepath)
    result_path.write_text(
        json.dumps(summary, indent=4) + "\n",
        encoding="utf-8",
    )

def config_logging(
    service_name: str,
    exec_log_only: bool = False,
    no_log: bool = False,
    bugs_mode: bool = False,
):
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

    bugs_filepath = None
    if bugs_mode:
        bugs_dir = Path(f"apis/bugs/{service_name}/{date}")
        bugs_dir.mkdir(parents=True, exist_ok=True)
        bugs_filepath = bugs_dir / "errors.json"

    hirest_handlers = ["console", "file"]
    executor_handlers = ["exec_file"]
    if exec_log_only:
        hirest_handlers = []
    if no_log:
        # no_log: keep only result_file output, disable normal log and exec_log.
        hirest_handlers = []
        executor_handlers = []

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
                "handlers": hirest_handlers,
                "propagate": False,
            },
            "hirest.fuzzer.executor": {
                "level": "DEBUG",
                "handlers": executor_handlers,
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
    paths = {
        "log_filepath": str(log_filepath),
        "exec_log_filepath": str(exec_log_filepath),
        "result_filepath": str(result_filepath),
    }
    if bugs_filepath is not None:
        paths["bugs_filepath"] = str(bugs_filepath)
    return paths


SERVICE = {
    "languagetool": {
        "base_url": "http://localhost:49981/v2/"
        # "base_url": "http://localhost:50101/v2/"
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
    },
    "user" : {
        "base_url": "http://localhost:50115/"
    },
    "genome" : {
        "base_url": "http://localhost:50110/"
    },
    "project" : {
        "base_url": "http://localhost:50118/"
    },
}

base_path = "/root/HiREST"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fuzzing REST APIs')
    parser.add_argument('--service', type=str, required=True, help='Name of the service to fuzz')
    parser.add_argument('--time_limit', type=int, default=3600, help='Time limit for fuzzing (seconds)')
    parser.add_argument('--requests', type=int, default=1000, help='Maximum number of requests')
    parser.add_argument('--exec-log-only', action='store_true', help='Disable normal logs and only keep exec_log output')
    parser.add_argument('--no-log', action='store_true', help='Disable normal log and exec_log, only keep result output')
    parser.add_argument('--BM', action='store_true', help='Enable BM mode: use primitive mutation operators instead of hierarchical space mutation')
    parser.add_argument('--bugs', action='store_true', help='Enable bugs mode: append every 5xx request/response pair to apis/bugs/<service>/<date>/errors.json in real time')
    parser.add_argument('--trend', action='store_true', help='Enable trend mode: dump JaCoCo coverage every 50 sent requests')
    parser.add_argument('--trend-interval', type=int, default=50, help='Trend dump interval in sent requests (default: 50)')
    args = parser.parse_args()

    if args.exec_log_only and args.no_log:
        parser.error('--exec-log-only and --no-log cannot be used together')

    def fuzzing_service(
        service_name: str,
        max_requests: int,
        time_limit: int,
        exec_log_only: bool = False,
        no_log: bool = False,
        bm_mode: bool = False,
        bugs_mode: bool = False,
        trend_mode: bool = False,
        trend_interval: int = 50,
    ):
        base_url = SERVICE[service_name]["base_url"]
        logging_paths = config_logging(
            service_name,
            exec_log_only=exec_log_only,
            no_log=no_log,
            bugs_mode=bugs_mode,
        )
        logger = logging.getLogger(__name__)

        input_space_manager = InputSpaceManager()
        misp_data = load_file(f"{base_path}/apis/{service_name}/partition/misp.json")
        input_space_manager.load_misps(misp_data)
        sisp_data = load_file(f"{base_path}/apis/{service_name}/partition/sisp.json")
        input_space_manager.load_sisps(sisp_data)
        input_space_manager.init_sisp_ss_failure_count()

        case_manager = CaseManager(input_space_manager)
        op_data = load_file(f"{base_path}/apis/{service_name}/op_slide/operation_template.json")
        case_manager.load_operations(op_data)
        seed_data = load_file(f"{base_path}/apis/{service_name}/seed/seed.json")
        case_manager.load_seeds(seed_data)

        if bm_mode:
            perturbation_mutator = PerturbationMutator()
            wrong_type_mutator = WrongTypeMutator()
            missing_required_mutator = MissingRequiredMutator()
            mutation_controller = PrimitiveMutationController(
                input_space_manager=input_space_manager,
                mutators=[
                    perturbation_mutator,
                    wrong_type_mutator,
                    missing_required_mutator,
                ],
            )
            logger.info("BM mode enabled: using PrimitiveMutationController with 3 primitive operators")
        else:
            sisp_mutator = SISPMutator()
            mispss_mutator = MISPSSMutator()
            misp_mutator = MISPMutator()
            mutation_controller = HierarchicalMutationController(
                input_space_manager=input_space_manager,
                mutators=[sisp_mutator, mispss_mutator, misp_mutator],
            )
        renderer = Renderer(base_url=base_url, bm_mode=bm_mode)
        executor = Executor()
        response_checker = RespChecker(
            summary_only=no_log,
            bugs_mode=bugs_mode,
            bugs_filepath=logging_paths.get("bugs_filepath"),
        )

        def run_jacoco_dump(reason: str) -> None:
            jacoco_script = Path(base_path) / "scripts" / "jacoco_dump.py"
            cmd = ["python", str(jacoco_script), service_name]
            try:
                logger.info(
                    "[trend] %s, running JaCoCo dump: %s",
                    reason,
                    " ".join(cmd),
                )
                subprocess.run(
                    cmd,
                    cwd=str(Path(base_path) / "scripts"),
                    check=True,
                )
            except Exception as exc:
                logger.error("[trend] JaCoCo dump failed (%s): %s", reason, exc)

        def on_request_sent(sent_count: int) -> None:
            if not trend_mode:
                return
            if trend_interval <= 0:
                return
            if sent_count % trend_interval != 0:
                return
            run_jacoco_dump(f"request_count={sent_count}")

        if trend_mode:
            # Baseline dump before sending any request.
            run_jacoco_dump("before_first_request")

        fuzzer = Fuzzer(
            input_space_manager=input_space_manager,
            case_manager=case_manager,
            mutation_controller=mutation_controller,
            renderer=renderer,
            executor=executor,
            response_checker=response_checker,
            max_requests=max_requests,
            time_limit=time_limit,
            on_request_sent=on_request_sent,
        )

        fuzzer.start()
        summary = response_checker.status_code_bucket.get("summary", {})
        if no_log:
            write_summary_result(logging_paths["result_filepath"], summary)
            print(f"[HiREST][RESULT] Summary-only result is saved in: {logging_paths['result_filepath']}")
            print("[HiREST][RESULT] Summary key path in JSON: $")
        else:
            print(f"[HiREST][RESULT] Summary result is saved in: {logging_paths['result_filepath']}")
            print("[HiREST][RESULT] Summary key path in JSON: summary")
        if bugs_mode:
            print(f"[HiREST][BUGS] 5xx errors are appended to: {logging_paths['bugs_filepath']}")

    fuzzing_service(
        args.service,
        args.requests,
        args.time_limit,
        args.exec_log_only,
        args.no_log,
        args.BM,
        args.bugs,
        args.trend,
        args.trend_interval,
    )

