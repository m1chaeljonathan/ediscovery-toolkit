import json
import logging

from openai import OpenAI

from config import load_config
from llm.sanitize import sanitize_input
from llm.schemas import validate_schema

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, base_url: str = None, model: str = None, api_key: str = None):
        cfg = load_config()['llm']
        self.client = OpenAI(
            base_url=base_url or cfg['base_url'],
            api_key=api_key or cfg.get('api_key', 'local'),
        )
        self.model = model or cfg['model']

    def extract(self, system_prompt: str, user_content: str, *,
                sanitize: bool = True, schema: dict = None,
                strict_schema: bool = False) -> dict:
        """Structured extraction — temperature 0, returns dict."""
        if sanitize:
            user_content, warnings = sanitize_input(user_content)
            if warnings:
                logger.info('Sanitized input before extraction: %s', warnings)

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
            data = json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text, "parse_error": True}

        if schema is not None:
            errors = validate_schema(data, schema, strict=strict_schema)
            if errors:
                logger.warning('Schema validation errors: %s', errors)
                data['_schema_errors'] = errors

        return data

    def generate(self, system_prompt: str, user_content: str, *,
                 sanitize: bool = True) -> str:
        """Plain-language generation — slightly higher temperature."""
        if sanitize:
            user_content, warnings = sanitize_input(user_content)
            if warnings:
                logger.info('Sanitized input before generation: %s', warnings)

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )
        return response.choices[0].message.content
