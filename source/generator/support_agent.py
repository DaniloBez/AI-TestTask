import os
import random
import json
from dotenv import load_dotenv

import logging
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam
)
import instructor
from pydantic import BaseModel, Field

from source.utils.api_handlers import retry_on_ratelimit

logger = logging.getLogger(__name__)

class SupportResponse(BaseModel):
    reply_text: str = Field(description="The support agent's message")

class SupportAgentData:
    def __init__(self, env_path: str = None, response_types_file: str = None, prompt_file: str = None):
        self.env_path = env_path
        self.response_types_file = response_types_file
        self.prompt_file = prompt_file
        self.response_types = []
        self.prompt_template = ""

        self._load_env()
        self._load_files()

    def _load_env(self):
        if self.env_path is None:
            self.env_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", ".env")
            )

        if os.path.exists(self.env_path):
            load_dotenv(dotenv_path=self.env_path)
        else:
            print(f"WARNING: .env file not found at {self.env_path}")

        self.api_key = os.getenv("SECRET_KEY")
        if not self.api_key:
            raise ValueError(f"SECRET_KEY not found in environment ({self.env_path})")

    def _load_files(self):
        self.response_types_file = self.response_types_file or self._default_response_types_path()
        self.prompt_file = self.prompt_file or self._default_prompt_path()

        self._validate_file(self.response_types_file)
        self._validate_file(self.prompt_file)

        self.load_response_types(self.response_types_file)
        self.load_prompt_template(self.prompt_file)

    @staticmethod
    def _validate_file(path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")

    def load_response_types(self, filepath: str):
        with open(filepath, "r", encoding="utf-8") as f:
            self.response_types = json.load(f)

    def load_prompt_template(self, filepath: str):
        with open(filepath, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()

    @staticmethod
    def _default_response_types_path() -> str:
        return os.path.join(os.path.dirname(__file__), "prompts", "support_agent_responses_types.json")

    @staticmethod
    def _default_prompt_path() -> str:
        return os.path.join(os.path.dirname(__file__), "prompts", "support_agent_prompt.txt")


class SupportAgent:

    def __init__(self, data, name: str = "SupportAgent", model: str = "openai/gpt-oss-120b"):
        self.name = name
        self.model = model or os.getenv("MODEL_NAME")
        self.response_types = data.response_types
        self.prompt_template = data.prompt_template
        self.messages: list[ChatCompletionMessageParam] = []

        if not data.api_key:
            raise ValueError("API key is required to initialize SupportAgent")

        self.client = instructor.from_openai(
            OpenAI(
                api_key=data.api_key,
                base_url="https://api.groq.com/openai/v1",
                max_retries=0
            ),
            mode=instructor.Mode.JSON
        )

        # Add initial system prompt
        system_prompt = self.prompt_template.format(
            conversation="",
            description="Initialize conversation"
        )
        self.messages.append(ChatCompletionSystemMessageParam(role="system", content=system_prompt))

    def choose_response_type(self) -> dict:
        if not self.response_types:
            logger.warning("response_types not loaded")
            return {"name": "normal", "description": "Gives a correct and helpful answer.", "chance": 1.0}
        weights = [r["chance"] for r in self.response_types]
        return random.choices(self.response_types, weights=weights, k=1)[0]

    def _build_prompt(self, client_message: str, current_messages: list) -> (str, dict):
        response_type = self.choose_response_type()
        description = response_type.get("description", "")

        temp_context = current_messages + [
            ChatCompletionUserMessageParam(role="user", content=client_message)
        ]

        conversation = "\n".join([f"{msg['role']}: {msg['content']}" for msg in temp_context])

        full_prompt = self.prompt_template.format(
            conversation=conversation,
            description=description
        )

        return full_prompt, response_type

    @retry_on_ratelimit()
    def _call_llm(self, prompt: str, client_message: str) -> str:
        clean_messages = self.messages + [
            ChatCompletionUserMessageParam(role="user", content=client_message),
            ChatCompletionSystemMessageParam(role="system", content=prompt)
        ]

        clean_messages = self._trim_messages(clean_messages)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=clean_messages,
            temperature=0.5,
            response_model=SupportResponse,
            max_retries=0
        )
        return response.reply_text

    def generate_next(self, client_message: str) -> (str, str):
        prompt, response_type = self._build_prompt(client_message, self.messages)

        response_text = self._call_llm(prompt, client_message)

        self.messages.append(ChatCompletionUserMessageParam(role="user", content=client_message))
        self.messages.append(ChatCompletionAssistantMessageParam(role="assistant", content=response_text))

        return response_text, response_type["name"]

    @staticmethod
    def _trim_messages(messages: list[ChatCompletionMessageParam], limit: int = 8) -> list[ChatCompletionMessageParam]:
        if len(messages) > limit:
            messages = [messages[0]] + messages[-6:]
            logger.info(f"Context trimmed to stay within token limits.")

        return messages

    def chat(self):
        print(f"Hello! I am {self.name}. Type 'exit' to end the chat.\n")
        while True:
            client_message = input("You: ").strip()
            if client_message.lower() in {"exit", "quit"}:
                print("Chat ended.")
                break
            reply, response_type = self.generate_next(client_message)
            print(f"{self.name} ({response_type}): {reply}\n")