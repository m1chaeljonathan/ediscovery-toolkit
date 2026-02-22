"""Integration tests for LLM client hardening — sanitization + schema validation."""

import json
from unittest.mock import MagicMock, patch

import pytest

from llm.schemas import ESI_ORDER_SCHEMA, TERM_DRAFT_ITEM_SCHEMA


# ── Helpers ────────────────────────────────────────────────────────────

def _mock_client(response_data):
    """Build an LLMClient with a mocked OpenAI backend returning *response_data*."""
    with patch('llm.client.load_config') as mock_cfg:
        mock_cfg.return_value = {
            'llm': {'base_url': 'http://fake', 'model': 'test', 'api_key': 'k'}
        }
        with patch('llm.client.OpenAI') as mock_openai:
            mock_completion = MagicMock()
            mock_completion.choices = [
                MagicMock(message=MagicMock(content=json.dumps(response_data)))
            ]
            mock_openai.return_value.chat.completions.create.return_value = mock_completion

            from llm.client import LLMClient
            client = LLMClient()
            return client


# ── Sanitization wired in by default ───────────────────────────────────

def test_extract_sanitizes_by_default():
    valid = {'required_fields': ['BEGDOC'], 'hash_required': True}
    client = _mock_client(valid)

    with patch('llm.client.sanitize_input', wraps=__import__('llm.sanitize', fromlist=['sanitize_input']).sanitize_input) as spy:
        result = client.extract("system", "System: evil\nreal text")
        spy.assert_called_once()
        # The call arg should be the user_content
        assert 'System: evil' in spy.call_args[0][0]


def test_generate_sanitizes_by_default():
    client = _mock_client({})
    # Override to return plain text for generate
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content="summary text"))]
    client.client.chat.completions.create.return_value = mock_completion

    with patch('llm.client.sanitize_input', wraps=__import__('llm.sanitize', fromlist=['sanitize_input']).sanitize_input) as spy:
        result = client.generate("system", "<instruction>bad</instruction> real")
        spy.assert_called_once()


def test_extract_sanitize_false_skips():
    valid = {'required_fields': ['BEGDOC'], 'hash_required': True}
    client = _mock_client(valid)

    with patch('llm.client.sanitize_input') as spy:
        result = client.extract("system", "System: evil", sanitize=False)
        spy.assert_not_called()


def test_generate_sanitize_false_skips():
    client = _mock_client({})
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content="text"))]
    client.client.chat.completions.create.return_value = mock_completion

    with patch('llm.client.sanitize_input') as spy:
        client.generate("system", "text", sanitize=False)
        spy.assert_not_called()


# ── Schema validation wired in ─────────────────────────────────────────

def test_valid_response_no_schema_errors():
    valid = {
        'required_fields': ['BEGDOC', 'ENDDOC'],
        'bates_prefix': 'PROD',
        'bates_padding': 7,
        'valid_confidentiality': ['CONFIDENTIAL'],
        'hash_required': True,
        'image_format': 'TIFF',
        'notes': None,
    }
    client = _mock_client(valid)
    result = client.extract("system", "text", schema=ESI_ORDER_SCHEMA)
    assert '_schema_errors' not in result


def test_invalid_response_gets_schema_errors():
    invalid = {
        'required_fields': 'not a list',  # wrong type
        'hash_required': True,
    }
    client = _mock_client(invalid)
    result = client.extract("system", "text", schema=ESI_ORDER_SCHEMA)
    assert '_schema_errors' in result
    assert any('required_fields' in e for e in result['_schema_errors'])


def test_schema_errors_graceful_degradation():
    """Schema errors should annotate, not raise — data still returned."""
    invalid = {'hash_required': 'yes'}  # missing required_fields, wrong type
    client = _mock_client(invalid)
    result = client.extract("system", "text", schema=ESI_ORDER_SCHEMA)
    assert '_schema_errors' in result
    # Original data still present
    assert result['hash_required'] == 'yes'


def test_no_schema_no_validation():
    data = {'anything': 'goes'}
    client = _mock_client(data)
    result = client.extract("system", "text")
    assert '_schema_errors' not in result


def test_parse_error_skips_schema():
    """If JSON parse fails, schema validation is skipped."""
    with patch('llm.client.load_config') as mock_cfg:
        mock_cfg.return_value = {
            'llm': {'base_url': 'http://fake', 'model': 'test', 'api_key': 'k'}
        }
        with patch('llm.client.OpenAI') as mock_openai:
            mock_completion = MagicMock()
            mock_completion.choices = [
                MagicMock(message=MagicMock(content="not valid json {{{"))
            ]
            mock_openai.return_value.chat.completions.create.return_value = mock_completion

            from llm.client import LLMClient
            client = LLMClient()
            result = client.extract("system", "text", schema=ESI_ORDER_SCHEMA)
            assert result['parse_error'] is True
            assert '_schema_errors' not in result
