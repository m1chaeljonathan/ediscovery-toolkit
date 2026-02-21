from parsers.schema import Document
from parsers.opt_parser import OptRecord
from modules.validators.bates import validate_bates
from modules.validators.family import validate_families
from modules.validators.coding import validate_coding
from modules.validators.crossref import validate_crossref


# --- Bates validator ---

def test_bates_no_issues_sequential():
    docs = [
        Document(begdoc='PROD0000001', enddoc='PROD0000001', source_row=2),
        Document(begdoc='PROD0000002', enddoc='PROD0000002', source_row=3),
        Document(begdoc='PROD0000003', enddoc='PROD0000003', source_row=4),
    ]
    assert validate_bates(docs) == []


def test_bates_detects_gap():
    docs = [
        Document(begdoc='PROD0000001', enddoc='PROD0000001', source_row=2),
        Document(begdoc='PROD0000003', enddoc='PROD0000003', source_row=3),
    ]
    issues = validate_bates(docs)
    assert len(issues) == 1
    assert issues[0].issue_type == 'gap'


def test_bates_detects_duplicate():
    docs = [
        Document(begdoc='PROD0000001', enddoc='PROD0000001', source_row=2),
        Document(begdoc='PROD0000001', enddoc='PROD0000001', source_row=3),
    ]
    issues = validate_bates(docs)
    assert any(i.issue_type == 'duplicate' for i in issues)


def test_bates_unsorted_input_detects_gap():
    """Bates validator should sort before checking gaps, not assume input order."""
    docs = [
        Document(begdoc='PROD0000003', enddoc='PROD0000003', source_row=4),
        Document(begdoc='PROD0000001', enddoc='PROD0000001', source_row=2),
        # PROD0000002 missing
    ]
    issues = validate_bates(docs)
    assert any(i.issue_type == 'gap' for i in issues)


def test_bates_wrong_prefix():
    docs = [Document(begdoc='PROD0000001', enddoc='PROD0000001', source_row=2)]
    issues = validate_bates(docs, expected_prefix='ABC')
    assert any(i.issue_type == 'format' for i in issues)


# --- Family validator ---

def test_family_no_issues():
    docs = [
        Document(begdoc='P0001', enddoc='P0001', begattach='P0001', endattach='P0003', source_row=2),
        Document(begdoc='P0002', enddoc='P0002', begattach='P0001', endattach='P0003', source_row=3),
        Document(begdoc='P0003', enddoc='P0003', begattach='P0001', endattach='P0003', source_row=4),
    ]
    assert validate_families(docs) == []


def test_family_orphan_detected():
    docs = [
        Document(begdoc='P0002', enddoc='P0002', begattach='P0001', endattach='P0003', source_row=2),
    ]
    issues = validate_families(docs)
    assert any(i.issue_type == 'orphan_attachment' for i in issues)


def test_family_broken_range():
    docs = [
        Document(begdoc='P0005', enddoc='P0005', begattach='P0005', endattach='P0002', source_row=2),
    ]
    issues = validate_families(docs)
    assert any(i.issue_type == 'broken_range' for i in issues)


# --- Coding validator ---

def test_coding_exact_match_privilege():
    """Should flag exact match 'PRIV', should NOT flag 'NOT PRIVILEGED'."""
    docs = [
        Document(begdoc='P0001', enddoc='P0001', privilege_code='PRIV', source_row=2),
        Document(begdoc='P0002', enddoc='P0002', privilege_code='NOT PRIVILEGED', source_row=3),
    ]
    issues = validate_coding(docs)
    flagged = {i.doc_id for i in issues}
    assert 'P0001' in flagged
    assert 'P0002' not in flagged


def test_coding_confidentiality_mismatch():
    docs = [
        Document(begdoc='P0001', enddoc='P0001', confidentiality='CLASSIFIED', source_row=2),
    ]
    issues = validate_coding(docs, valid_confidentiality={'CONFIDENTIAL'})
    assert any(i.issue_type == 'confidentiality_mismatch' for i in issues)


# --- Cross-reference validator ---

def test_crossref_missing_in_opt():
    docs = [Document(begdoc='P0001', enddoc='P0001')]
    opts = []
    issues = validate_crossref(docs, opts)
    assert any(i.issue_type == 'missing_in_opt' for i in issues)


def test_crossref_missing_in_dat():
    docs = []
    opts = [OptRecord(begdoc='P0001', volume='V1', image_path='', first_page=True, page_count=1)]
    issues = validate_crossref(docs, opts)
    assert any(i.issue_type == 'missing_in_dat' for i in issues)
