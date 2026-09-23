"""
Logging centralizado: consola + archivo rotativo por ejecución.
"""

import logging
import os
from datetime import datetime

from src.config import APP_CONFIG


def get_logger(name: str) -> logging.Logger:
    os.makedirs(APP_CONFIG.log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:  # evita duplicar handlers si se llama más de una vez
        return logger

    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)

    log_file = os.path.join(
        APP_CONFIG.log_dir, f"run_{datetime.now():%Y%m%d_%H%M%S}.log"
    )
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
