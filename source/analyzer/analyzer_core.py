import json
import os
import time
from openai import OpenAI
from dotenv import load_dotenv
from source.analyzer.prompts.analyzer_prompts import SYSTEM_PROMPT
from source.utils.validation.check_llm_output import is_valid_output
from source.utils.logger_config import setup_logger

load_dotenv()
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
log_file_path = os.path.join(project_root, "data", "analyzer.log")
logger = setup_logger(log_file_path)

client = OpenAI(
    api_key=os.environ.get("SECRET_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


def analyze_single_chat(chat_messages, max_retries=3):
    chat_text = "\n".join([f"{msg['author']}: {msg['text']}" for msg in chat_messages])

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=os.environ.get("MODEL_NAME"),
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze this chat:\n\n{chat_text}"}
                ],
                temperature=0.0,
                seed=42,
                response_format={"type": "json_object"}
            )

            response_text = response.choices[0].message.content
            data = json.loads(response_text)

            if is_valid_output(data):
                return data
            else:
                logger.warning(f"Attempt {attempt + 1}: Data failed logical validation. Retrying...")

        except json.JSONDecodeError:
            logger.error(f"Attempt {attempt + 1}: Model returned invalid JSON format. Retrying...")
        except Exception as e:
            logger.error(f"Attempt {attempt + 1}: API Error - {e}")

        time.sleep(1)

    logger.critical("Failed to get a valid response after all attempts.")
    return None


def analyze():
    dataset_path = os.path.join(project_root, "data", "dataset.json")
    result_path = os.path.join(project_root, "data", "result.json")

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    results = []

    for item in dataset.get("data", []):
        chat_id = item["id"]
        logger.info(f"Analyzing chat ID: {chat_id}...")

        analysis_data = analyze_single_chat(item["chat"])

        if analysis_data:
            final_obj = {"id": chat_id}
            final_obj.update(analysis_data)
            results.append(final_obj)
            logger.info(f"Chat ID {chat_id} analyzed successfully.")
        else:
            results.append({"id": chat_id, "error": "Failed to analyze"})
            logger.error(f"Chat ID {chat_id} failed to analyze.")

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"Done! Results saved to {result_path}")