import os
import random
import json
from groq import Groq
from dotenv import load_dotenv





class SupportAgent:
    def __init__(
        self,
        name: str = "SupportAgent",
        model: str = "openai/gpt-oss-120b",
        api_key: str = None,
        env_path: str = None,
        response_types_file: str = None,
        prompt_file: str = None
    ):
        self.name = name
        self.model = model
        self.messages = []
        self.response_types = []
        self.prompt_template = ""
        
        api_key = self._load_api_key(api_key, env_path)
        self._init_client(api_key)
        self._load_files(response_types_file, prompt_file)

    
    def _load_api_key(self, api_key: str = None, env_path: str = None) -> str:
        if api_key:
            return api_key

        if env_path is None:
            env_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", ".env")
            )

        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)
        else:
            print(f"WARNING: .env file not found at {env_path}")

        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise ValueError(f"GROQ_API_KEY not found in environment ({env_path})")

        return key
    
    def _init_client(self, api_key: str):
        if not api_key:
            raise ValueError("API key is required to initialize SupportAgent")
        self.client = Groq(api_key=api_key)

    def load_response_types(self, filepath: str):
        with open(filepath, "r", encoding="utf-8") as f:
            self.response_types = json.load(f)

    def load_prompt_template(self, filepath: str):
        with open(filepath, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()
    
    def _load_files(self, response_types_file: str, prompt_file: str):
        response_types_file = (
            response_types_file
            or self._default_response_types_path()
        )

        prompt_file = (
            prompt_file
            or self._default_prompt_path()
        )

        self._validate_file(response_types_file)
        self._validate_file(prompt_file)

        self.load_response_types(response_types_file)
        self.load_prompt_template(prompt_file)


    def _get_base_dir(self) -> str:
        return os.path.dirname(os.path.abspath(__file__))

    def _default_response_types_path(self) -> str:
        return os.path.join(os.path.dirname(__file__), "prompts", "support_agent_responses_types.json")

    def _default_prompt_path(self) -> str:
        return os.path.join(os.path.dirname(__file__), "prompts", "support_agent_prompt.txt")

    def _validate_file(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")

    def choose_response_type(self) -> dict:
        if not self.response_types:
            print("WARNING response_types were not imported")
            return {"name": "normal", "description": "Gives a correct and helpful answer.", "chance": 1.0}

        weights = [r["chance"] for r in self.response_types]
        return random.choices(self.response_types, weights=weights, k=1)[0]

    def _build_prompt(self, client_message: str) -> (list, dict):
        response_type = self.choose_response_type()
        description = response_type.get("description", "")

        self.messages.append({"role": "user", "content": client_message, "response_type": None})

        conversation_text = ""
        for msg in self.messages:
            role = "User" if msg["role"] == "user" else "Support"
            conversation_text += f"{role}: {msg['content']}\n"

        full_prompt = self.prompt_template.format(
            conversation=conversation_text,
            description=description
        )

        return full_prompt, response_type

    def _call_llm(self, prompt: str) -> str:
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_completion_tokens=600,
                top_p=0.9,
                stream=False
            )

            message = completion.choices[0].message

            if not message.content:
                print("WARNING: Model returned empty content")
                return ""

            return message.content.strip()

        except Exception as e:
            print("LLM ERROR:", e)
            return ""

    def generate_next(self, client_message: str) -> (str, str):
        prompt, response_type = self._build_prompt(client_message)
        response_text = self._call_llm(prompt)

        self.messages.append({"role": "assistant", "content": response_text, "response_type": response_type["name"]})
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

