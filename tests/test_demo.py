"""End-to-end tests using demo-scale fixtures (50 docs, 5 custodians)."""
from modules.production_qc import run_production_qc
from modules.intake_qc import run_intake_qc

DEMO_DAT = 'tests/fixtures/demo_production.dat'
DEMO_OPT = 'tests/fixtures/demo_production.opt'
PURVIEW = 'tests/fixtures/purview_intake.csv'


def test_demo_production_has_expected_doc_count():
    result = run_production_qc(DEMO_DAT)
    assert result['stats']['total_documents'] == 49  # 50 minus 1 gap doc removed


def test_demo_production_detects_privilege():
    result = run_production_qc(DEMO_DAT)
    coding = result['issues']['coding']
    priv_docs = [i for i in coding if i['issue_type'] == 'privileged_in_production']
    assert len(priv_docs) >= 1


def test_demo_production_detects_bates_gap():
    result = run_production_qc(DEMO_DAT)
    assert result['stats']['bates_issues'] > 0


def test_demo_production_detects_crossref_issues():
    result = run_production_qc(DEMO_DAT, DEMO_OPT)
    assert result['stats']['crossref_issues'] > 0


def test_demo_production_detects_bad_confidentiality():
    result = run_production_qc(
        DEMO_DAT,
        spec={'valid_confidentiality': [
            'CONFIDENTIAL',
            'HIGHLY CONFIDENTIAL - ATTORNEYS EYES ONLY',
        ]}
    )
    coding = result['issues']['coding']
    conf_issues = [i for i in coding if i['issue_type'] == 'confidentiality_mismatch']
    assert len(conf_issues) >= 1


def test_purview_intake_flags_missing_standard_fields():
    result = run_intake_qc(PURVIEW, required_fields=['BEGDOC', 'ENDDOC', 'CUSTODIAN'])
    types = {i['issue_type'] for i in result['issues']}
    assert 'missing_required_field' in types


def test_purview_intake_detects_nonstandard_headers():
    result = run_intake_qc(PURVIEW)
    headers = result['headers_received']
    # Purview uses different header names
    assert 'Item ID' in headers
    assert 'BEGDOC' not in headers
