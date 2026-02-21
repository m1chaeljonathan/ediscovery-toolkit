from dataclasses import dataclass

from parsers.schema import Document

# Common privilege coding values across platforms — exact match only
PRIVILEGE_CODES = {
    'PRIV', 'PRIVILEGE', 'ACP', 'WP', 'WORK PRODUCT',
    'ATTORNEY CLIENT', 'AC', 'WITHHOLD', 'WITHHELD', 'REDACTED-PRIV',
}

PII_CODES = {'PII', 'PERSONAL', 'HIPAA', 'PHI', 'SENSITIVE'}


@dataclass
class CodingIssue:
    doc_id: str
    row: int
    issue_type: str
    field: str
    value: str
    detail: str


def validate_coding(documents: list[Document],
                    valid_confidentiality: set[str] = None) -> list[CodingIssue]:
    issues = []
    for doc in documents:
        # Check privilege flag — exact match to avoid "NOT PRIVILEGED" false positives
        priv = doc.privilege_code.upper().strip()
        if priv and priv in PRIVILEGE_CODES:
            issues.append(CodingIssue(
                doc.begdoc, doc.source_row, 'privileged_in_production',
                'PRIVILEGE', doc.privilege_code,
                f"Document coded as '{doc.privilege_code}' — should not be produced"
            ))

        # Check confidentiality designation valid
        if valid_confidentiality and doc.confidentiality:
            normalized = {v.upper() for v in valid_confidentiality}
            if doc.confidentiality.upper() not in normalized:
                issues.append(CodingIssue(
                    doc.begdoc, doc.source_row, 'confidentiality_mismatch',
                    'CONFIDENTIALITY', doc.confidentiality,
                    f"'{doc.confidentiality}' not in allowed values: {valid_confidentiality}"
                ))

    return issues
