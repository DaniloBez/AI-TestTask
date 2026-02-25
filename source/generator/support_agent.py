import os
import random
import logging

from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
)
import instructor
from pydantic import BaseModel, Field

from source.utils.api_handlers import retry_on_ratelimit

from source.generator.prompts.support_agent_responses_types import RESPONSE_TYPES
from source.generator.prompts.support_agent_prompt import SUPPORT_AGENT_PROMPT
logger = logging.getLogger(__name__)
#logging.basicConfig(
#    level=logging.INFO,
#    format="%(asctime)s [%(levelname)s] %(message)s"
#)

class SupportResponse(BaseModel):
    reply_text: str = Field(description="The support agent's message")

class SupportAgent:
    def __init__(self, name: str = "SupportAgent", model: str = "openai/gpt-oss-120b"):
        self.name = name
        self.model = model or os.getenv("MODEL_NAME")
        self.api_key = os.getenv("SECRET_KEY")
        self.response_types = RESPONSE_TYPES
        self.prompt_template = SUPPORT_AGENT_PROMPT
        self.messages: list[ChatCompletionMessageParam] = []

        if not self.api_key:
            raise ValueError("SECRET_KEY is required to initialize SupportAgent")

        self.client = instructor.from_openai(
            OpenAI(api_key=self.api_key, base_url="https://api.groq.com/openai/v1"),
            mode=instructor.Mode.JSON
        )

        system_prompt = self.prompt_template.format(conversation="", description="Initialize conversation")
        self.messages.append(ChatCompletionSystemMessageParam(role="system", content=system_prompt))

        logger.info(f"SupportAgent initialized: {self.name} using model {self.model}")
        logger.info(f"Loaded {len(self.response_types)} response types")

    def choose_response_type(self) -> dict:
        if not self.response_types:
            logger.warning("response_types not loaded")
            return {"name": "normal", "description": "Gives a correct and helpful answer.", "chance": 1.0}
        weights = [r["chance"] for r in self.response_types]
        choice = random.choices(self.response_types, weights=weights, k=1)[0]
        logging.info(f"Support Agent chose the following response style: {choice}")
        return choice

    def _build_prompt(self, client_message: str) -> (str, dict):
        response_type = self.choose_response_type()
        description = response_type.get("description", "")

        self.messages.append({"role": "user", "content": client_message})

        conversation = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.messages])

        full_prompt = self.prompt_template.format(
            conversation=conversation,
            description=description
        )
        logging.info(f"Prompt built: {full_prompt}")
        return full_prompt, response_type

    def _call_llm(self, prompt: str) -> str:

        clean_messages = self.messages + [
            ChatCompletionSystemMessageParam(role="system", content=prompt)
        ]
        logging.info("Sending request to LLM...")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=clean_messages,
            temperature=0.5,
            max_tokens=1600,
            response_model=SupportResponse
        )
        logging.info(f"Support Agent answered: {response.reply_text}")
        return response.reply_text

    @retry_on_ratelimit()
    def generate_next(self, client_message: str) -> (str, str):
        logging.info(f"Support Agent received the following message: {client_message}")
        prompt, response_type = self._build_prompt(client_message)
        response_text = self._call_llm(prompt)

        self.messages.append({
            "role": "assistant",
            "content": response_text,
           # "response_type": response_type["name"]
        })

        return response_text, response_type["name"]

    def chat(self):
        print(f"Hello! I am {self.name}. Type 'exit' to end the chat.\n")
        while True:
            client_message = input("You: ").strip()
            if client_message.lower() in {"exit", "quit"}:
                print("Chat ended.")
                break
            reply, response_type = self.generate_next(client_message)
            print(f"{self.name} ({response_type}): {reply}\n")