from modules.production_qc import run_production_qc

CLEAN = 'tests/fixtures/clean_production.dat'
ISSUES = 'tests/fixtures/issue_production.dat'


def test_clean_production_passes():
    result = run_production_qc(CLEAN, spec={'valid_confidentiality': ['CONFIDENTIAL']})
    assert result['stats']['passed'] is True
    assert result['stats']['coding_issues'] == 0


def test_issue_production_fails():
    result = run_production_qc(ISSUES, spec={'valid_confidentiality': ['CONFIDENTIAL']})
    assert result['stats']['passed'] is False


def test_privilege_flag_detected():
    result = run_production_qc(ISSUES, spec={'valid_confidentiality': ['CONFIDENTIAL']})
    assert result['stats']['coding_issues'] > 0


def test_duplicate_bates_detected():
    result = run_production_qc(ISSUES)
    assert result['stats']['bates_issues'] > 0


def test_confidentiality_mismatch_detected():
    result = run_production_qc(ISSUES, spec={'valid_confidentiality': ['CONFIDENTIAL']})
    coding = result['issues']['coding']
    types = {i['issue_type'] for i in coding}
    assert 'confidentiality_mismatch' in types
