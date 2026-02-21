"""Generate synthetic eDiscovery test fixtures covering all QC scenarios."""
from pathlib import Path

delim, qual = '\x14', '\xfe'
out = Path(__file__).parent / 'fixtures'
out.mkdir(exist_ok=True)


def make_row(values):
    return delim.join(f'{qual}{v}{qual}' for v in values)


headers = [
    'BEGDOC', 'ENDDOC', 'BEGATTACH', 'ENDATTACH', 'CUSTODIAN',
    'DATE_SENT', 'FILE_EXTENSION', 'MD5_HASH', 'CONFIDENTIALITY', 'PRIVILEGE',
]

# --- sample.dat: minimal fixture for parser tests ---
sample_rows = [
    ['PROD0000001', 'PROD0000001', '', '', 'Smith, John', '', '', '', 'CONFIDENTIAL', ''],
    ['PROD0000002', 'PROD0000002', '', '', 'Jones, Mary', '', '', '', '', 'PRIV'],
]
with open(out / 'sample.dat', 'w', encoding='utf-8-sig') as f:
    f.write(make_row(headers) + '\n')
    for row in sample_rows:
        f.write(make_row(row) + '\n')

# --- clean_production.dat: should PASS all QC checks ---
clean_rows = [
    ['PROD0000001', 'PROD0000001', 'PROD0000001', 'PROD0000003', 'Smith, John',
     '01/15/2024', 'MSG', 'abc123', 'CONFIDENTIAL', ''],
    ['PROD0000002', 'PROD0000002', 'PROD0000001', 'PROD0000003', 'Smith, John',
     '01/16/2024', 'PDF', 'def456', 'CONFIDENTIAL', ''],
    ['PROD0000003', 'PROD0000003', 'PROD0000001', 'PROD0000003', 'Smith, John',
     '01/17/2024', 'PDF', 'ghi789', 'CONFIDENTIAL', ''],
]
with open(out / 'clean_production.dat', 'w', encoding='utf-8-sig') as f:
    f.write(make_row(headers) + '\n')
    for row in clean_rows:
        f.write(make_row(row) + '\n')

# --- issue_production.dat: should FAIL with multiple issue types ---
issue_rows = [
    ['PROD0000001', 'PROD0000001', '', '', 'Jones, Mary',
     '01/15/2024', 'MSG', '', 'CONFIDENTIAL', ''],
    ['PROD0000001', 'PROD0000001', '', '', 'Jones, Mary',
     '01/16/2024', 'PDF', '', 'CONFIDENTIAL', ''],  # Duplicate Bates
    ['PROD0000003', 'PROD0000003', '', '', 'Jones, Mary',
     '01/17/2024', 'PDF', '', 'CLASSIFIED', 'PRIV'],  # Privileged + bad confidentiality
]
with open(out / 'issue_production.dat', 'w', encoding='utf-8-sig') as f:
    f.write(make_row(headers) + '\n')
    for row in issue_rows:
        f.write(make_row(row) + '\n')

# --- sample_privlog.csv: privilege log fixture ---
privlog_headers = ['DATE', 'AUTHOR', 'RECIPIENTS', 'DOC_TYPE', 'PRIVILEGE_BASIS']
privlog_rows = [
    ['01/15/2024', 'Smith, John', 'Jones, Mary', 'Email', 'ACP'],
    ['01/16/2024', 'Smith, John', '', 'Memo', 'WP'],  # Blank RECIPIENTS
    ['01/17/2024', 'Doe, Jane', 'Smith, John', 'Email', 'MADE UP'],  # Invalid basis
]
with open(out / 'sample_privlog.csv', 'w', encoding='utf-8') as f:
    f.write(','.join(privlog_headers) + '\n')
    for row in privlog_rows:
        f.write(','.join(row) + '\n')

print('Test fixtures created:')
for p in sorted(out.iterdir()):
    if p.is_file():
        print(f'  {p.name}')
