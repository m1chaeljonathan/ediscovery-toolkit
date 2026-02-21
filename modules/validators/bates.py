import re
from dataclasses import dataclass


@dataclass
class BatesIssue:
    doc_id: str
    row: int
    issue_type: str   # 'format', 'duplicate', 'gap', 'sequence'
    detail: str


def _extract_bates_parts(bates: str):
    """Extract (prefix, number_str, number_int) from a Bates number, or None."""
    match = re.match(r'^([A-Za-z_\-\.]+)(\d+)$', bates)
    if not match:
        return None
    return match.group(1), match.group(2), int(match.group(2))


def validate_bates(documents, expected_prefix: str = None,
                   expected_padding: int = None) -> list[BatesIssue]:
    issues = []
    seen = {}

    # Parse all Bates numbers first
    parsed = []
    for doc in documents:
        bates = doc.begdoc
        parts = _extract_bates_parts(bates)
        if parts is None:
            issues.append(BatesIssue(bates, doc.source_row, 'format',
                f"'{bates}' does not match expected prefix+number pattern"))
            continue
        prefix, num_str, num = parts

        # Check expected prefix if provided
        if expected_prefix and prefix != expected_prefix:
            issues.append(BatesIssue(bates, doc.source_row, 'format',
                f"Expected prefix '{expected_prefix}', found '{prefix}'"))

        # Check padding consistency
        if expected_padding and len(num_str) != expected_padding:
            issues.append(BatesIssue(bates, doc.source_row, 'format',
                f"Expected {expected_padding}-digit padding, found {len(num_str)}"))

        # Check duplicates
        if bates in seen:
            issues.append(BatesIssue(bates, doc.source_row, 'duplicate',
                f"Duplicate of row {seen[bates]}"))
        else:
            seen[bates] = doc.source_row

        parsed.append((prefix, num, doc.source_row, bates))

    # Sort by prefix then number before checking gaps — DAT files aren't
    # guaranteed to be sorted by Bates number
    parsed.sort(key=lambda x: (x[0], x[1]))

    for i in range(1, len(parsed)):
        prev_prefix, prev_num, _, _ = parsed[i - 1]
        curr_prefix, curr_num, curr_row, curr_bates = parsed[i]

        if curr_prefix == prev_prefix and curr_num != prev_num + 1:
            issues.append(BatesIssue(curr_bates, curr_row, 'gap',
                f"Gap: expected {prev_num + 1}, found {curr_num}"))

    return issues
