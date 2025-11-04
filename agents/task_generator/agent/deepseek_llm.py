from typing import Optional, List
import requests
from langchain.llms.base import LLM
from langchain.schema import SystemMessage, HumanMessage
from config import Config


class DeepSeekLLM(LLM):
    """ Custom LLM wrapper for DeepSeek API """
    api_key: str
    model: str
    temperature: float
    base_url: str

    def __init__(
            self, api_key: str,
            model: str = Config.DEEPSEEK_MODEL,
            temperature: float = Config.DEEPSEEK_TEMPERATURE,
            base_url: str = Config.DEEPSEEK_BASE_URL
    ):
        super().__init__(api_key=api_key, model=model, temperature=temperature, base_url=base_url)
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.base_url = base_url

    @property
    def _llm_type(self) -> str:
        return "deepseek"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": 2048
        }
        response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    def _generate(self, messages: List, stop: Optional[List[str]] = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        api_messages = []
        for msg in messages:
            if hasattr(msg, 'content'):
                if isinstance(msg, SystemMessage):
                    api_messages.append({"role": "system", "content": msg.content})
                elif isinstance(msg, HumanMessage):
                    api_messages.append({"role": "user", "content": msg.content})
                else:
                    api_messages.append({"role": "user", "content": str(msg)})

        payload = {
            "model": self.model,
            "messages": api_messages,
            "temperature": self.temperature,
            "max_tokens": 4096
        }

        response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
