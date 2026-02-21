from modules.privilege_log_qc import run_privilege_log_qc

FIXTURE = 'tests/fixtures/sample_privlog.csv'


def test_privlog_detects_blank_required_field():
    result = run_privilege_log_qc(FIXTURE)
    types = {i['issue_type'] for i in result['issues']}
    assert 'blank_required_field' in types


def test_privlog_detects_invalid_basis():
    result = run_privilege_log_qc(FIXTURE)
    types = {i['issue_type'] for i in result['issues']}
    assert 'invalid_privilege_basis' in types


def test_privlog_reports_correct_entry_count():
    result = run_privilege_log_qc(FIXTURE)
    assert result['stats']['total_entries'] == 5
