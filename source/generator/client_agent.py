import logging

import instructor
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionAssistantMessageParam, ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from pydantic import BaseModel, Field

import source.generator.prompts.client_agent_prompts as prompts
import os

from ..utils.api_handlers import retry_on_ratelimit
from ..utils.app_config import ValidSatisfactionLevels, MIN_QUALITY_SCORE, MAX_QUALITY_SCORE

logger = logging.getLogger(__name__)

class ClientResponse(BaseModel):
    reply_text: str = Field(description="Your message to the agent.")
    is_resolved: bool = Field(description="True if you want to end the conversation because you have been helped, or you are angry and do not want to talk anymore")
    emotion: str = Field(description="Your current emotion, for example: calm, angry, confused")
    satisfaction: ValidSatisfactionLevels = Field(description="Your PERSONAL satisfaction. Are you happy with your current situation?")
    quality_score: int = Field(description="Professional evaluation of the agent's response. Did they follow protocol? Were they polite? Or were they robotic/rude?", ge=MIN_QUALITY_SCORE, le=MAX_QUALITY_SCORE)

class OverallQualityResponse(BaseModel):
    quality_score: int = Field(description="Professional evaluation of the agent's response. Did they follow protocol? Were they polite? Or were they robotic/rude?", ge=MIN_QUALITY_SCORE, le=MAX_QUALITY_SCORE)

class ClientAgent:
    def __init__(self, situation: str, personality: str):
        self.model = os.getenv("MODEL_NAME")

        logging.info(f"Initializing ClientAgent. Model: {self.model}")
        logging.info(f"Personality: {personality}")
        logging.info(f"Situation: {situation}")

        self.client = instructor.from_openai(
            OpenAI(
                api_key=os.getenv("SECRET_KEY"),
                base_url=os.getenv("BASE_URL"),
                max_retries=0
            ),
            mode=instructor.Mode.JSON
        )
        self.messages: list[ChatCompletionMessageParam] = [
            ChatCompletionSystemMessageParam(role="system", content=prompts.BASIC_PROMPT.format(personality=personality, situation=situation)),
        ]

    @staticmethod
    def _trim_messages(messages: list[ChatCompletionMessageParam], limit: int = 6) -> list[ChatCompletionMessageParam]:
        if len(messages) > limit:
            messages = [messages[0]] + messages[-4:]
            logger.info("Context trimmed to stay within token limits.")

        return messages

    @retry_on_ratelimit()
    def generate_next(self, message: str) -> ClientResponse:
        logging.info(f"ClientAgent received message: {message}")

        messages_to_send = self.messages + [
            ChatCompletionUserMessageParam(role="user", content=message)
        ]

        #messages_to_send = self._trim_messages(messages_to_send)

        logging.info("Sending request to LLM...")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages_to_send,
            temperature=0.5,
            response_model=ClientResponse,
            max_retries=0
        )

        logging.info(f"ClientAgent generated response: {response.reply_text} | is_resolved: {response.is_resolved}")
        logging.info(f"Client emotion: {response.emotion}, satisfaction: {response.satisfaction}, assessment of support's work: {response.quality_score}")

        self.messages.append(ChatCompletionUserMessageParam(role="user", content=message))
        self.messages.append(ChatCompletionAssistantMessageParam(role="assistant", content=response.reply_text))
        return response