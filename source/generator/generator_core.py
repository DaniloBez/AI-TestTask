import json
import logging
import random

from .client_agent import ClientAgent
from .prompts.client_agent_prompts import PERSONALITIES, SITUATIONS
from .support_agent import SupportAgent

logger = logging.getLogger(__name__)


def generate_datasets(n_conversations: int = 5):
    logger.info(f"Starting generation of {n_conversations} conversations...")

    all_chats = []
    all_stats = []

    for i in range(1, n_conversations + 1):
        try:
            chat_data, meta_data = generate_dataset(i)
            all_chats.append(chat_data)
            all_stats.append(meta_data)
            logger.info(f"Progress: {i}/{n_conversations} generated.")
        except Exception as e:
            logger.error(f"Skipping conversation #{i} due to error: {e}")

    with open("./data/dataset.json", "w", encoding="utf-8") as f:
        json.dump({"data": all_chats}, f, ensure_ascii=False, indent=2)

    with open("./data/validation.json", "w", encoding="utf-8") as f:
        json.dump(all_stats, f, ensure_ascii=False, indent=2)

    logger.info("Generation complete.")


def generate_dataset(conv_id: int) -> tuple[dict, dict]:
    sit_key = random.choice(list(SITUATIONS.keys()))
    situation = SITUATIONS[sit_key]
    personality = random.choice(PERSONALITIES)

    client = ClientAgent(situation, personality)

    support = SupportAgent()

    chat_history = []
    agent_mistakes = []

    initial_greeting = "Hello! Welcome to customer support. How can I help you today?"
    chat_history.append({"author": "agent", "text": initial_greeting})

    try:
        client_response = client.generate_next(initial_greeting)
        chat_history.append({"author": "client", "text": client_response.reply_text})

        is_end = client_response.is_resolved
        last_satisfaction = client_response.satisfaction
        last_quality_score = client_response.quality_score

        while not is_end:
            agent_reply, response_type = support.generate_next(client_message=client_response.reply_text)
            chat_history.append({"author": "agent", "text": agent_reply})

            if response_type != "normal":
                agent_mistakes.append(response_type)

            client_response = client.generate_next(agent_reply)
            chat_history.append({"author": "client", "text": client_response.reply_text})

            is_end = client_response.is_resolved
            last_satisfaction = client_response.satisfaction
            last_quality_score = client_response.quality_score

            if len(chat_history) > 20:
                logger.warning(f"Conversation {conv_id} exceeded turn limit. Forcing termination.")
                break

        chat_data = {
            "id": conv_id,
            "chat": chat_history
        }

        meta_data = {
            "id": conv_id,
            "intent": sit_key,
            "satisfaction": last_satisfaction.value if hasattr(last_satisfaction, 'value') else str(last_satisfaction),
            "quality_score": last_quality_score,
            "agent_mistakes": list(set(agent_mistakes))
        }

        logger.info(f"Conversation {conv_id} finished")

        return chat_data, meta_data
    except Exception as e:
        logger.error(f"Conversation {conv_id} failed. Error: {e}")
        raise e
