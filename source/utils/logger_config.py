import logging
from logging import Logger


def setup_logger(filename: str) -> Logger:
    log_filename = filename

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_filename, mode="w", encoding="utf-8"),
        ],
        force=True
    )

    print(f"Logs are written to: {log_filename}")

    return logging.getLogger(__name__)