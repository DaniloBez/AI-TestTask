import os
import random
import logging
import instructor
from pydantic import BaseModel, Field
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
)

from source.utils.api_handlers import retry_on_ratelimit
from source.generator.prompts.support_agent_responses_types import RESPONSE_TYPES
from source.generator.prompts.support_agent_prompt import SUPPORT_AGENT_PROMPT

logger = logging.getLogger(__name__)

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

    def _build_prompt(self, client_message: str) -> tuple[str, dict]:
        response_type = self.choose_response_type()
        description = response_type.get("description", "")

        temp_history = self.messages + [
            ChatCompletionUserMessageParam(role="user", content=client_message)
        ]

        conversation = "\n".join([f"{msg['role']}: {msg['content']}" for msg in temp_history])

        full_prompt = self.prompt_template.format(
            conversation=conversation,
            description=description
        )
        return full_prompt, response_type

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

    @retry_on_ratelimit()
    def generate_next(self, client_message: str) -> tuple[str, str]:
        logger.info(f"Generating response for: {client_message[:50]}...")

        prompt, response_type = self._build_prompt(client_message)

        response_text = self._call_llm(prompt, client_message)

        self.messages.append(ChatCompletionUserMessageParam(role="user", content=client_message))
        self.messages.append(ChatCompletionAssistantMessageParam(role="assistant", content=response_text))

        return response_text, response_type["name"]

    @staticmethod
    def _trim_messages(messages: list[ChatCompletionMessageParam], limit: int = 6) -> list[ChatCompletionMessageParam]:
        if len(messages) > limit:
            messages = [messages[0]] + messages[-4:]
            logger.info("Context trimmed to stay within token limits.")

        return messages