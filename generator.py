from dotenv import load_dotenv
from source.utils.logger_config import setup_logger

load_dotenv()
logger = setup_logger("generator.log")

def main():
    print("Generator started")

if __name__ == "__main__":
    main()