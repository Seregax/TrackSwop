import logging
import sys
from pathlib import Path

SIMPLE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%H:%M:%S"


def setup_logger(log_file: str = "app.log", level=logging.INFO):
    log_path = Path(log_file).parent
    if log_path != Path("."):
        log_path.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    root_logger.handlers.clear()

    formatter = logging.Formatter(SIMPLE_FORMAT, DATE_FORMAT)

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    return root_logger


def get_logger(name: str):
    """Get logger for module"""
    return logging.getLogger(name)
