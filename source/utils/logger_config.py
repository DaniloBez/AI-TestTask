import logging
import os
from logging import Logger


def setup_logger(filename: str, logger_name: str = __name__) -> Logger:
    # Ensure logs directory exists
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # Avoid adding multiple handlers if the logger already has them
    if not logger.handlers:
        file_handler = logging.FileHandler(filename, mode="w", encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.propagate = False

    print(f"Logs are written to: {filename}")

    return logger