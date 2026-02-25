from dotenv import load_dotenv
from support_agent import SupportAgentData, SupportAgent
load_dotenv()
def main():
    data = SupportAgentData()
    agent = SupportAgent(data, name="Bot")
    agent.chat()


if __name__ == "__main__":
    main()