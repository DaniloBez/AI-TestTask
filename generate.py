from dotenv import load_dotenv
from source.generator.generator_core import generate_datasets
from source.utils.logger_config import setup_logger

import os

load_dotenv()

project_root = os.path.dirname(os.path.abspath(__file__))
logger = setup_logger(os.path.join(project_root, "logs", "generator.log"), "source.generator")

if __name__ == "__main__":
    generate_datasets(50)