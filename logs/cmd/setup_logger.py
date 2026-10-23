import logging
import sys
from pathlib import Path


def get_logger(
    name: str = __name__,
    log_file: str | None = "app.log",
    level: int = logging.INFO,
) -> logging.Logger:
    """Configura e retorna uma instância do Logger padrão do Python.

    Evita duplicar handlers caso seja chamado múltiplas vezes para o mesmo módulo.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # if the logger already has handlers configured, just return it
    if logger.hasHandlers():
        return logger

    # formatat: date/hour | level | module:line | message
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 1. output handler at Terminal (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. file handler
    if log_file:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(log_dir / log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # prevent messages from being duplicated at the root logger
    logger.propagate = False

    return logger
