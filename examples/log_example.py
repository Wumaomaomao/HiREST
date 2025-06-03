import logging

from pathlib import Path
from datetime import datetime

from examples.common import config_logging

config_logging(
    service_name="languagetool"
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")