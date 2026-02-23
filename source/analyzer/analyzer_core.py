import json
import os
import time
from openai import OpenAI
from dotenv import load_dotenv
from source.analyzer.prompts.analyzer_prompts import SYSTEM_PROMPT
from source.utils.validation.check_llm_output import is_valid_output

load_dotenv()
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
                print(f"[Warning] Attempt {attempt + 1}: Data failed logical validation. Retrying...")

        except json.JSONDecodeError:
            print(f"[Error] Attempt {attempt + 1}: Model returned invalid JSON format. Retrying...")
        except Exception as e:
            print(f"[API Error] Attempt {attempt + 1}: {e}")

        time.sleep(1)

    print("[Critical] Failed to get a valid response after all attempts.")
    return None


def analyze():
    dataset_path = os.path.join(project_root, "data", "dataset.json")
    result_path = os.path.join(project_root, "data", "result.json")

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    results = []

    for item in dataset.get("data", []):
        chat_id = item["id"]
        print(f"Analyzing chat ID: {chat_id}...")

        analysis_data = analyze_single_chat(item["chat"])

        if analysis_data:
            final_obj = {"id": chat_id}
            final_obj.update(analysis_data)
            results.append(final_obj)
            print(f"[Success] Chat ID {chat_id} analyzed.")
        else:
            results.append({"id": chat_id, "error": "Failed to analyze"})

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Results saved to {result_path}")