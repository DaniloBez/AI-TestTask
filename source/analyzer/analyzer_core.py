import os
import json
import instructor
from typing import List
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

from source.analyzer.prompts.analyzer_prompts import SYSTEM_PROMPT
from source.utils.logger_config import setup_logger
from source.utils.app_config import ValidSatisfactionLevels, MIN_QUALITY_SCORE, MAX_QUALITY_SCORE
from source.utils.api_handlers import retry_on_ratelimit

load_dotenv()
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
log_file_path = os.path.join(project_root, "data", "analyzer.log")
logger = setup_logger(log_file_path)


class AnalysisResponse(BaseModel):
    intent: str = Field(
        description="The category of the issue, e.g., 'payment issues', 'technical errors', etc., or 'other'")
    satisfaction: ValidSatisfactionLevels = Field(
        description="Client's final satisfaction level")
    quality_score: int = Field(ge=MIN_QUALITY_SCORE, le=MAX_QUALITY_SCORE,
                               description=f"Agent's work quality score from {MIN_QUALITY_SCORE} to {MAX_QUALITY_SCORE}")
    agent_mistakes: List[str] = Field(default_factory=list,
                                      description="List of agent mistakes (e.g., 'ignored_question'). Empty list if none.")


client = instructor.from_openai(
    OpenAI(
        api_key=os.environ.get("SECRET_KEY"),
        base_url="https://openrouter.ai/api/v1"
    ),
    mode=instructor.Mode.JSON
)


@retry_on_ratelimit()
def analyze_single_chat(chat_messages):
    chat_text = "\n".join([f"{msg['author']}: {msg['text']}" for msg in chat_messages])

    messages = [
        ChatCompletionSystemMessageParam(role="system", content=SYSTEM_PROMPT),
        ChatCompletionUserMessageParam(role="user", content=f"Analyze this chat:\n\n{chat_text}")
    ]

    response: AnalysisResponse = client.chat.completions.create(
        model=os.environ.get("MODEL_NAME"),
        response_model=AnalysisResponse,
        messages=messages,
        temperature=0.0,
        seed=42,
        max_retries=3
    )

    return response.model_dump()


def analyze():
    dataset_path = os.path.join(project_root, "data", "dataset.json")
    result_path = os.path.join(project_root, "data", "result.json")

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    results = []

    for item in dataset.get("data", []):
        chat_id = item["id"]
        logger.info(f"Analyzing chat ID: {chat_id}...")

        try:
            analysis_data = analyze_single_chat(item["chat"])

            final_obj = {"id": chat_id}
            final_obj.update(analysis_data)
            results.append(final_obj)
            logger.info(f"Chat ID {chat_id} analyzed successfully.")

        except Exception as e:
            results.append({"id": chat_id, "error": "Failed to analyze"})
            logger.error(f"Chat ID {chat_id} failed to analyze after all retries. Error: {e}")

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"Done! Results saved to {result_path}")