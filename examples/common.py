import logging
import logging.config
import json
from datetime import datetime
from pathlib import Path

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
    """Custom JSON formatter for CoSREST.fuzzer.response_checker."""

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
            # "cosrest": {
            #     "level": "DEBUG",
            #     "handlers": ["console", "file"],
            #     "propagate": False,
            # },
            # "cosrest.fuzzer.executor": {
            #     "level": "DEBUG",
            #     "handlers": ["exec_file"],
            #     "propagate": False,
            # },
            "cosrest.fuzzer.resp_checker": {
                "level": "DEBUG",
                "handlers": ["result_file"],  # 输出到 result_file
                "propagate": False,
            },
        }
    }

    logging.config.dictConfig(LOGGING_CONFIG)
