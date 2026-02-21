"""Generate synthetic eDiscovery test fixtures covering all QC scenarios.

Creates:
  sample.dat              — minimal parser test (2 docs)
  clean_production.dat    — should PASS all QC (3 docs, 1 family)
  clean_production.opt    — matching OPT for cross-ref
  issue_production.dat    — should FAIL: dupes, privilege, bad confidentiality, gaps
  demo_production.dat     — demo-scale realistic production (50 docs, 5 custodians)
  demo_production.opt     — matching OPT (with 2 intentional mismatches)
  purview_intake.csv      — Purview-style export with ISO dates and non-standard headers
  sample_privlog.csv      — privilege log with conformity issues
"""
import csv
import hashlib
import random
from pathlib import Path

delim, qual = '\x14', '\xfe'
out = Path(__file__).parent / 'fixtures'
out.mkdir(exist_ok=True)

random.seed(42)  # reproducible


def make_row(values):
    return delim.join(f'{qual}{v}{qual}' for v in values)


HEADERS = [
    'BEGDOC', 'ENDDOC', 'BEGATTACH', 'ENDATTACH', 'CUSTODIAN',
    'DATE_SENT', 'FILE_EXTENSION', 'MD5_HASH', 'CONFIDENTIALITY', 'PRIVILEGE',
]

CUSTODIANS = [
    'Smith, John', 'Jones, Mary', 'Williams, Robert',
    'Davis, Sarah', 'Chen, David',
]
EXTENSIONS = ['MSG', 'PDF', 'DOCX', 'XLSX', 'PPTX', 'TXT', 'PNG', 'EML']
CONF_VALUES = ['CONFIDENTIAL', 'HIGHLY CONFIDENTIAL - ATTORNEYS EYES ONLY']


def make_hash(s):
    return hashlib.md5(s.encode()).hexdigest()


# ---------------------------------------------------------------------------
# sample.dat — minimal parser test
# ---------------------------------------------------------------------------
sample_rows = [
    ['PROD0000001', 'PROD0000001', '', '', 'Smith, John', '', '', '', 'CONFIDENTIAL', ''],
    ['PROD0000002', 'PROD0000002', '', '', 'Jones, Mary', '', '', '', '', 'PRIV'],
]
with open(out / 'sample.dat', 'w', encoding='utf-8-sig') as f:
    f.write(make_row(HEADERS) + '\n')
    for row in sample_rows:
        f.write(make_row(row) + '\n')


# ---------------------------------------------------------------------------
# clean_production.dat + clean_production.opt — should PASS all QC
# ---------------------------------------------------------------------------
clean_rows = [
    ['PROD0000001', 'PROD0000001', 'PROD0000001', 'PROD0000003', 'Smith, John',
     '01/15/2024', 'MSG', make_hash('1'), 'CONFIDENTIAL', ''],
    ['PROD0000002', 'PROD0000002', 'PROD0000001', 'PROD0000003', 'Smith, John',
     '01/16/2024', 'PDF', make_hash('2'), 'CONFIDENTIAL', ''],
    ['PROD0000003', 'PROD0000003', 'PROD0000001', 'PROD0000003', 'Smith, John',
     '01/17/2024', 'PDF', make_hash('3'), 'CONFIDENTIAL', ''],
]
with open(out / 'clean_production.dat', 'w', encoding='utf-8-sig') as f:
    f.write(make_row(HEADERS) + '\n')
    for row in clean_rows:
        f.write(make_row(row) + '\n')

with open(out / 'clean_production.opt', 'w') as f:
    writer = csv.writer(f)
    for i, row in enumerate(clean_rows):
        bates = row[0]
        writer.writerow([bates, 'VOL001', f'IMAGES\\{bates}.tif', 'Y', 1])


# ---------------------------------------------------------------------------
# issue_production.dat — should FAIL with multiple issue types
# ---------------------------------------------------------------------------
issue_rows = [
    ['PROD0000001', 'PROD0000001', '', '', 'Jones, Mary',
     '01/15/2024', 'MSG', '', 'CONFIDENTIAL', ''],
    ['PROD0000001', 'PROD0000001', '', '', 'Jones, Mary',
     '01/16/2024', 'PDF', '', 'CONFIDENTIAL', ''],           # duplicate Bates
    ['PROD0000003', 'PROD0000003', '', '', 'Jones, Mary',
     '01/17/2024', 'PDF', '', 'CLASSIFIED', 'PRIV'],          # privilege + bad conf
]
with open(out / 'issue_production.dat', 'w', encoding='utf-8-sig') as f:
    f.write(make_row(HEADERS) + '\n')
    for row in issue_rows:
        f.write(make_row(row) + '\n')


# ---------------------------------------------------------------------------
# demo_production.dat + demo_production.opt — realistic demo scale
# 50 documents, 5 custodians, 8 families, intentional issues:
#   - 1 privileged doc in production (DEMO0000025)
#   - 1 bad confidentiality value (DEMO0000040)
#   - 2 OPT mismatches (DEMO0000048 missing from OPT, DEMO0000099 in OPT only)
#   - 1 Bates gap (DEMO0000030 missing — jumps 29→31)
#   - 1 orphan attachment (DEMO0000045 parent DEMO0000044 not in set)
# ---------------------------------------------------------------------------
demo_docs = []
doc_num = 1
families = []

# Generate 8 family groups of 3-5 docs each
for fam_idx in range(8):
    fam_size = random.randint(3, 5)
    parent = f'DEMO{doc_num:07d}'
    end_attach = f'DEMO{doc_num + fam_size - 1:07d}'
    custodian = CUSTODIANS[fam_idx % len(CUSTODIANS)]
    month = (fam_idx % 12) + 1
    for j in range(fam_size):
        bates = f'DEMO{doc_num:07d}'
        ext = 'MSG' if j == 0 else random.choice(EXTENSIONS[1:])
        date = f'{month:02d}/{15 + j:02d}/2024'
        row = [
            bates, bates, parent, end_attach, custodian,
            date, ext, make_hash(bates), random.choice(CONF_VALUES), '',
        ]
        demo_docs.append(row)
        doc_num += 1

# Fill remaining standalone docs up to 50
while len(demo_docs) < 50:
    bates = f'DEMO{doc_num:07d}'
    custodian = random.choice(CUSTODIANS)
    date = f'{random.randint(1,12):02d}/{random.randint(1,28):02d}/2024'
    ext = random.choice(EXTENSIONS)
    row = [
        bates, bates, '', '', custodian,
        date, ext, make_hash(bates), random.choice(CONF_VALUES), '',
    ]
    demo_docs.append(row)
    doc_num += 1

# Inject issues
# 1. Privileged doc
demo_docs[24][9] = 'PRIV'  # PRIVILEGE field

# 2. Bad confidentiality
demo_docs[39][8] = 'TOP SECRET'

# 3. Orphan attachment — point to non-existent parent
demo_docs[44][2] = 'DEMO9999999'  # BEGATTACH
demo_docs[44][3] = 'DEMO9999999'  # ENDATTACH

# 4. Remove doc at index 29 to create Bates gap (29→31)
gap_doc = demo_docs.pop(29)

with open(out / 'demo_production.dat', 'w', encoding='utf-8-sig') as f:
    f.write(make_row(HEADERS) + '\n')
    for row in demo_docs:
        f.write(make_row(row) + '\n')

# OPT — match all docs except skip one DAT doc and add one extra
with open(out / 'demo_production.opt', 'w') as f:
    writer = csv.writer(f)
    for i, row in enumerate(demo_docs):
        bates = row[0]
        if bates == 'DEMO0000048':
            continue  # missing from OPT — will trigger crossref issue
        writer.writerow([bates, 'VOL001', f'IMAGES\\{bates}.tif', 'Y', 1])
    # Extra OPT entry with no DAT match
    writer.writerow(['DEMO0000099', 'VOL001', 'IMAGES\\DEMO0000099.tif', 'Y', 1])


# ---------------------------------------------------------------------------
# purview_intake.csv — Purview-style export with non-standard headers + ISO dates
# ---------------------------------------------------------------------------
purview_headers = [
    'Item ID', 'Subject', 'Sender', 'Recipients', 'Date',
    'Has attachment', 'Item class', 'Sensitivity label',
]
purview_rows = [
    ['AAMkADE...001', 'Q3 Revenue Discussion', 'smith@corp.com',
     'jones@corp.com; davis@corp.com', '2024-03-15T14:30:00Z',
     'True', 'IPM.Note', 'Confidential'],
    ['AAMkADE...002', 'Re: Q3 Revenue Discussion', 'jones@corp.com',
     'smith@corp.com', '2024-03-15T15:02:00Z',
     'False', 'IPM.Note', 'Confidential'],
    ['AAMkADE...003', 'Budget Projections FY25', 'davis@corp.com',
     'williams@corp.com', '2024-04-01T09:00:00Z',
     'True', 'IPM.Note', 'Highly Confidential'],
    ['AAMkADE...004', 'Team Offsite Planning', 'chen@corp.com',
     'all-hands@corp.com', '2024-04-10T11:30:00Z',
     'False', 'IPM.Note', ''],
    ['AAMkADE...005', '', 'smith@corp.com',
     'jones@corp.com', '2024-05-20T08:15:00Z',
     'False', 'IPM.Note', 'Confidential'],  # blank subject
]
with open(out / 'purview_intake.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(purview_headers)
    for row in purview_rows:
        writer.writerow(row)


# ---------------------------------------------------------------------------
# sample_privlog.csv — privilege log with conformity issues
# ---------------------------------------------------------------------------
privlog_headers = ['DATE', 'AUTHOR', 'RECIPIENTS', 'DOC_TYPE', 'PRIVILEGE_BASIS']
privlog_rows = [
    ['01/15/2024', 'Smith, John', 'Jones, Mary', 'Email', 'ACP'],
    ['01/16/2024', 'Smith, John', '', 'Memo', 'WP'],               # blank RECIPIENTS
    ['01/17/2024', 'Doe, Jane', 'Smith, John', 'Email', 'MADE UP'],  # invalid basis
    ['01/18/2024', 'Williams, Robert', 'Chen, David', 'Letter', 'ATTORNEY-CLIENT'],
    ['', 'Davis, Sarah', 'Smith, John', 'Email', 'COMMON INTEREST'],  # blank DATE
]
with open(out / 'sample_privlog.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(privlog_headers)
    for row in privlog_rows:
        writer.writerow(row)


# ---------------------------------------------------------------------------
print('Test fixtures created:')
for p in sorted(out.iterdir()):
    if p.is_file():
        size = p.stat().st_size
        print(f'  {p.name:30s} {size:>8,} bytes')
