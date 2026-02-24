"""Module E — Litigation Readiness: LLM-powered generation.

Data map generation, hold analysis, and preservation memo generation.
Follows the same pattern as modules/term_generator/generator.py.
"""

import json
from dataclasses import asdict
from pathlib import Path

from llm.client import LLMClient
from llm.schemas import AI_DATAMAP_SCHEMA, AI_HOLD_ANALYSIS_SCHEMA
from modules.ai_lithold import DataType, LegalHold

_PROMPTS = Path(__file__).parent.parent / 'llm' / 'prompts'


def _prompt(name: str) -> str:
    return (_PROMPTS / name).read_text()


def generate_data_map(company_description: str,
                      client: LLMClient = None) -> dict:
    """Generate a suggested data map from a company description.

    Returns raw LLM output dict with company_type, data_types, notes.
    Caller is responsible for converting to DataType instances after user review.
    """
    client = client or LLMClient()
    return client.extract(
        _prompt('ai_datamap_generate.txt'),
        f"COMPANY DESCRIPTION:\n\n{company_description[:6000]}",
        schema=AI_DATAMAP_SCHEMA,
    )


def analyze_hold_scenario(scenario: str, data_types: list[DataType],
                          client: LLMClient = None) -> dict:
    """Analyze a litigation scenario against the current data map.

    Returns raw LLM output dict with scenario_type, affected_data_type_ids, etc.
    """
    client = client or LLMClient()
    dt_summary = json.dumps(
        [{"id": dt.id, "name": dt.name, "category": dt.category,
          "description": dt.description}
         for dt in data_types],
        indent=2)
    user_content = (
        f"SCENARIO:\n{scenario[:3000]}\n\n"
        f"DATA MAP:\n{dt_summary}"
    )
    return client.extract(
        _prompt('ai_hold_analysis.txt'),
        user_content,
        schema=AI_HOLD_ANALYSIS_SCHEMA,
    )


def generate_preservation_memo(hold: LegalHold, data_types: list[DataType],
                               client: LLMClient = None) -> str:
    """Generate a preservation scope memo from structured hold data.

    Returns Markdown-formatted memo text.
    """
    client = client or LLMClient()
    dt_lookup = {dt.id: asdict(dt) for dt in data_types}
    affected = [dt_lookup[dtid] for dtid in hold.affected_data_types
                if dtid in dt_lookup]
    user_content = (
        f"MATTER: {hold.scenario}\n"
        f"SCENARIO TYPE: {hold.scenario_type}\n"
        f"HOLD SCOPE: {hold.hold_scope_summary}\n"
        f"ESTIMATED VOLUME: {hold.estimated_volume}\n"
        f"CUSTODIANS: {json.dumps(hold.custodians)}\n"
        f"PRESERVATION ACTIONS: {json.dumps(hold.preservation_actions)}\n"
        f"PRIVILEGE CONSIDERATIONS: {json.dumps(hold.privilege_considerations)}\n"
        f"CROSS-BORDER FLAGS: {json.dumps(hold.cross_border_flags)}\n\n"
        f"AFFECTED DATA TYPES:\n{json.dumps(affected, indent=2)}"
    )
    return client.generate(_prompt('ai_preservation_memo.txt'), user_content)
