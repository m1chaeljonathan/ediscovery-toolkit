import csv
from pathlib import Path
from dataclasses import dataclass, asdict

import openpyxl


@dataclass
class PrivLogIssue:
    row: int
    issue_type: str   # 'missing_column', 'blank_required_field', 'invalid_privilege_basis'
    field: str = ""
    detail: str = ""


COMMON_PRIVILEGE_BASES = {
    'ACP', 'ATTORNEY-CLIENT', 'ATTORNEY CLIENT PRIVILEGE',
    'WP', 'WORK PRODUCT', 'ATTORNEY WORK PRODUCT',
    'COMMON INTEREST', 'JOINT DEFENSE',
}


def _load_log(filepath: str) -> tuple[list[str], list[dict]]:
    path = Path(filepath)
    if path.suffix.lower() in ('.xlsx', '.xls'):
        wb = openpyxl.load_workbook(filepath, read_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        headers = [str(h).strip() if h else '' for h in rows[0]]
        records = [
            dict(zip(headers, [str(v).strip() if v else '' for v in row]))
            for row in rows[1:]
        ]
        return headers, records
    else:
        with open(filepath, encoding='utf-8-sig', errors='replace') as f:
            reader = csv.DictReader(f)
            records = list(reader)
            headers = reader.fieldnames or []
            return list(headers), records


def run_privilege_log_qc(log_path: str, required_columns: list[str] = None,
                         valid_privilege_bases: set[str] = None,
                         output_dir: str = "./reports/output") -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    required_columns = required_columns or [
        'DATE', 'AUTHOR', 'RECIPIENTS', 'DOC_TYPE', 'PRIVILEGE_BASIS',
    ]
    valid_bases = valid_privilege_bases or COMMON_PRIVILEGE_BASES
    issues = []

    headers, records = _load_log(log_path)

    # Check required columns present
    for col in required_columns:
        if col not in headers:
            issues.append(PrivLogIssue(0, 'missing_column', field=col,
                detail=f"Required column '{col}' not found in privilege log"))

    for row_num, record in enumerate(records, start=2):
        for col in required_columns:
            if col in headers and not record.get(col, '').strip():
                issues.append(PrivLogIssue(row_num, 'blank_required_field',
                    field=col, detail=f"Row {row_num}: '{col}' is blank"))

        # Privilege basis validation
        basis = record.get('PRIVILEGE_BASIS', '').upper().strip()
        if basis and basis not in valid_bases:
            issues.append(PrivLogIssue(row_num, 'invalid_privilege_basis',
                field='PRIVILEGE_BASIS',
                detail=f"Row {row_num}: '{record.get('PRIVILEGE_BASIS')}' not a recognized basis"))

    stats = {
        'total_entries': len(records),
        'total_issues': len(issues),
        'passed': len(issues) == 0,
    }

    return {'issues': [asdict(i) for i in issues], 'stats': stats, 'headers': headers}
