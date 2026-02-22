from pathlib import Path

import pdfplumber

from llm.client import LLMClient
from llm.schemas import ESI_ORDER_SCHEMA, PRIVLOG_SPEC_SCHEMA


def _load_prompt(name: str) -> str:
    path = Path(__file__).parent / 'prompts' / name
    return path.read_text()


def extract_esi_spec(pdf_path: str, client: LLMClient = None) -> dict:
    """Extract production spec from ESI order PDF. Returns structured dict."""
    client = client or LLMClient()

    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""

    if not text.strip():
        return {"error": "No text extracted from PDF — may be image-based, try OCR"}

    system_prompt = _load_prompt('esi_order_extract.txt')
    spec = client.extract(system_prompt, f"ESI ORDER TEXT:\n\n{text[:8000]}",
                          schema=ESI_ORDER_SCHEMA)
    spec['source_file'] = Path(pdf_path).name
    return spec


def extract_privlog_spec(pdf_path: str, client: LLMClient = None) -> dict:
    """Extract privilege log requirements from order PDF."""
    client = client or LLMClient()

    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""

    if not text.strip():
        return {"error": "No text extracted from PDF"}

    system_prompt = _load_prompt('privlog_spec_extract.txt')
    spec = client.extract(system_prompt, f"ORDER TEXT:\n\n{text[:8000]}",
                          schema=PRIVLOG_SPEC_SCHEMA)
    spec['source_file'] = Path(pdf_path).name
    return spec
