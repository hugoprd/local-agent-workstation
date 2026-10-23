import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def get_log_path_name(name: str) -> str:
    """
    returns the log path name based on the provided name.
    """
    words: list[str] = name.split("_")

    final_words: list[str] = []
    for word in words:
        final_words.append(word)

        if word == "tool":
            break

    final_name: str = "_".join(final_words)

    return final_name


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
    file_name = log_file if log_file else f"{name}.log"
    path_name = get_log_path_name(name)
    log_path = ROOT_DIR / path_name
    log_path.mkdir(parents=True, exist_ok=True)

    log_path = ROOT_DIR / path_name / file_name

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.propagate = False

    return logger
