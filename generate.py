from dotenv import load_dotenv
from source.generator.generator_core import generate_datasets
from source.utils.logger_config import setup_logger

load_dotenv()

logger = setup_logger("generator.log")

if __name__ == "__main__":
    generate_datasets(1)