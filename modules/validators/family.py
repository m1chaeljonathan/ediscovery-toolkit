import re
from dataclasses import dataclass

from parsers.schema import Document


@dataclass
class FamilyIssue:
    doc_id: str
    row: int
    issue_type: str   # 'orphan_attachment', 'missing_attachment', 'broken_range'
    detail: str


def _extract_numeric(bates: str) -> int | None:
    """Extract the trailing numeric portion from a Bates number."""
    match = re.search(r'(\d+)$', bates)
    return int(match.group(1)) if match else None


def validate_families(documents: list[Document]) -> list[FamilyIssue]:
    issues = []
    all_begdocs = {doc.begdoc for doc in documents}

    for doc in documents:
        if not doc.begattach or not doc.endattach:
            continue

        # Verify parent is present if this is an attachment
        if doc.begattach != doc.begdoc and doc.begattach not in all_begdocs:
            issues.append(FamilyIssue(
                doc.begdoc, doc.source_row, 'orphan_attachment',
                f"Parent {doc.begattach} not found in production set"
            ))

        # Verify BEGATTACH <= ENDATTACH using numeric extraction
        begin_num = _extract_numeric(doc.begattach)
        end_num = _extract_numeric(doc.endattach)
        if begin_num is not None and end_num is not None and begin_num > end_num:
            issues.append(FamilyIssue(
                doc.begdoc, doc.source_row, 'broken_range',
                f"BEGATTACH {doc.begattach} > ENDATTACH {doc.endattach}"
            ))

    return issues
