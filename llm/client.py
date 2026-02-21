import json

from openai import OpenAI

from config import load_config


class LLMClient:
    def __init__(self, base_url: str = None, model: str = None, api_key: str = None):
        cfg = load_config()['llm']
        self.client = OpenAI(
            base_url=base_url or cfg['base_url'],
            api_key=api_key or cfg.get('api_key', 'local'),
        )
        self.model = model or cfg['model']

    def extract(self, system_prompt: str, user_content: str) -> dict:
        """Structured extraction — temperature 0, returns dict."""
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
        )
        text = response.choices[0].message.content
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text, "parse_error": True}

    def generate(self, system_prompt: str, user_content: str) -> str:
        """Plain-language generation — slightly higher temperature."""
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )
        return response.choices[0].message.content
