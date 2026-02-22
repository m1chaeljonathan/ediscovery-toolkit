import json
from pathlib import Path

from llm.client import LLMClient
from modules.term_generator.name_proximity import generate_name_terms

_PROMPTS = Path(__file__).parent.parent.parent / 'llm' / 'prompts'
_LIBS    = Path(__file__).parent / 'libraries'


def _prompt(name: str) -> str:
    return (_PROMPTS / name).read_text()


def _library(domain: str) -> dict:
    p = _LIBS / f"{domain}.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _parse_list(result) -> list:
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        for key in ('terms', 'search_terms', 'results', 'data'):
            if isinstance(result.get(key), list):
                return result[key]
    return []


def extract_concepts(text: str, client: LLMClient = None) -> dict:
    client = client or LLMClient()
    return client.extract(
        _prompt('term_concept_extract.txt'),
        f"CASE TEXT:\n\n{text[:6000]}"
    )


def draft_terms(concepts: dict, seed_terms: list[str] = None,
                client: LLMClient = None) -> list[dict]:
    client = client or LLMClient()
    lib = _library(concepts.get('industry_domain', 'general'))
    ctx = f"CONCEPTS:\n{json.dumps(concepts, indent=2)}\n\n"
    if lib:
        ctx += (f"DOMAIN LIBRARY ({lib.get('domain', '')}):\n"
                f"Common terms: {lib.get('common_terms', [])}\n"
                f"Specialist terms: {lib.get('specialist_terms', [])}\n"
                f"Known false positives: {lib.get('false_positive_patterns', [])}\n")
    if seed_terms:
        ctx += "\nSEED TERMS:\n" + "\n".join(seed_terms)

    return _parse_list(
        client.extract(_prompt('term_draft.txt'), ctx)
    )


def generate(case_text: str,
             seed_terms: list[str] = None) -> tuple[dict, list[dict]]:
    """Full two-stage pipeline. Returns (concepts, terms)."""
    client = LLMClient()
    concepts = extract_concepts(case_text, client)
    terms = draft_terms(concepts, seed_terms, client)
    terms.extend(generate_name_terms(concepts.get('named_entities', [])))
    return concepts, terms
