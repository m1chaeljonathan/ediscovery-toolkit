import json
from pathlib import Path
from dataclasses import asdict

from parsers.dat_parser import parse_dat
from parsers.opt_parser import parse_opt
from modules.validators.bates import validate_bates
from modules.validators.family import validate_families
from modules.validators.coding import validate_coding
from modules.validators.crossref import validate_crossref
from llm.client import LLMClient


def run_production_qc(dat_path: str, opt_path: str = None,
                      spec: dict = None, output_dir: str = "./reports/output") -> dict:
    """
    Run full production QC pipeline.

    spec keys: expected_prefix, expected_padding, valid_confidentiality
    Returns dict with all issues and stats.
    """
    spec = spec or {}
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Parse
    dat_result = parse_dat(dat_path)
    opt_records = parse_opt(opt_path) if opt_path else []
    docs = dat_result.documents

    # Run validators
    bates_issues = validate_bates(
        docs,
        expected_prefix=spec.get('expected_prefix'),
        expected_padding=spec.get('expected_padding'),
    )
    family_issues = validate_families(docs)
    coding_issues = validate_coding(
        docs,
        valid_confidentiality=set(spec.get('valid_confidentiality', [])) or None,
    )
    crossref_issues = validate_crossref(docs, opt_records) if opt_records else []

    # Compile results
    all_issues = {
        'bates': [asdict(i) for i in bates_issues],
        'family': [asdict(i) for i in family_issues],
        'coding': [asdict(i) for i in coding_issues],
        'crossref': [asdict(i) for i in crossref_issues],
    }
    stats = {
        'total_documents': dat_result.row_count,
        'encoding_detected': dat_result.encoding_detected,
        'parse_errors': len(dat_result.errors),
        'bates_issues': len(bates_issues),
        'family_issues': len(family_issues),
        'coding_issues': len(coding_issues),
        'crossref_issues': len(crossref_issues),
        'total_issues': sum(len(v) for v in all_issues.values()),
        'passed': sum(len(v) for v in all_issues.values()) == 0,
    }

    with open(output_dir / 'stats.json', 'w') as f:
        json.dump(stats, f, indent=2)

    return {'issues': all_issues, 'stats': stats, 'parse_errors': dat_result.errors}


def generate_qc_summary(qc_result: dict, client: LLMClient = None) -> str:
    """Generate a counsel-ready QC summary memo using the LLM.

    Takes the output of run_production_qc and returns plain-text memo.
    """
    client = client or LLMClient()
    prompt_path = Path(__file__).parent.parent / 'llm' / 'prompts' / 'qc_summary.txt'
    system_prompt = prompt_path.read_text()

    # Format issues into a readable block for the LLM
    stats = qc_result['stats']
    issues = qc_result['issues']

    lines = [
        f"Total documents: {stats['total_documents']}",
        f"Overall status: {'PASSED' if stats['passed'] else 'FAILED'}",
        f"Encoding detected: {stats['encoding_detected']}",
        "",
    ]

    for category, items in issues.items():
        if items:
            lines.append(f"--- {category.upper()} ISSUES ({len(items)}) ---")
            for item in items:
                detail = item.get('detail', '')
                doc_id = item.get('doc_id', item.get('doc_id', ''))
                lines.append(f"  [{doc_id}] {detail}")
            lines.append("")

    user_content = "\n".join(lines)
    return client.generate(system_prompt, user_content)
