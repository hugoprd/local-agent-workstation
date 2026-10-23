import logging
import sys
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "files"


def get_logger(
    name: str = __name__,
    log_file: str | None = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    configures and returns an instance of the standard Python Logger.

    saves each log file separately within the specified directory.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.hasHandlers():
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 1. exibition handler at the Terminal (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. file handler
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    file_name = log_file if log_file else f"{name}.log"
    log_path = LOG_DIR / file_name

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.propagate = False

    return logger
