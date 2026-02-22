"""Input sanitization for LLM prompts — defends against prompt injection."""

import re
import logging

logger = logging.getLogger(__name__)

# Directive-like line starters (case-insensitive, at start of line)
_DIRECTIVE_RE = re.compile(
    r'^\s*(System|Instruction|Prompt|Assistant|Human|User|AI|Bot)\s*:.*$',
    re.IGNORECASE | re.MULTILINE,
)

# XML/HTML-style role tags
_TAG_RE = re.compile(
    r'<\s*/?\s*(system|instruction|prompt|assistant|human|user|role|command)\s*>',
    re.IGNORECASE,
)

# Explicit "ignore previous instructions" phrases
_IGNORE_RE = re.compile(
    r'ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions|prompts|directives|rules)',
    re.IGNORECASE,
)

# Delimiter floods (5+ consecutive characters)
_DELIMITER_RE = re.compile(r'[#=\-]{5,}')

_REPLACEMENT = '[REMOVED: potential directive]'


def sanitize_input(text: str) -> tuple[str, list[str]]:
    """Detect and neutralize common prompt-injection patterns in user-supplied text.

    Returns (sanitized_text, warnings) where warnings lists each detection.
    Legal text mentioning "instructions" in normal prose is preserved.
    """
    warnings: list[str] = []

    def _replace(pattern, label, src):
        nonlocal warnings
        hits = pattern.findall(src)
        if hits:
            warnings.append(f'{label}: {len(hits)} match(es)')
            src = pattern.sub(_REPLACEMENT, src)
        return src

    result = text
    result = _replace(_DIRECTIVE_RE, 'directive_line', result)
    result = _replace(_TAG_RE, 'role_tag', result)
    result = _replace(_IGNORE_RE, 'ignore_instruction', result)
    result = _replace(_DELIMITER_RE, 'delimiter_flood', result)

    if warnings:
        logger.warning('Sanitization triggered: %s', '; '.join(warnings))

    return result, warnings
