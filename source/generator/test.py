from dotenv import load_dotenv
from support_agent import SupportAgent
load_dotenv()
def main():
    agent = SupportAgent(name="Bot")
    agent.chat()


if __name__ == "__main__":
    main()