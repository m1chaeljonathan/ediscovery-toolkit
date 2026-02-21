from modules.intake_qc import run_intake_qc

FIXTURE = 'tests/fixtures/sample.dat'


def test_intake_passes_with_available_fields():
    result = run_intake_qc(FIXTURE, required_fields=['BEGDOC', 'ENDDOC', 'CUSTODIAN'])
    assert result['stats']['passed'] is True


def test_intake_flags_missing_field():
    result = run_intake_qc(FIXTURE, required_fields=['BEGDOC', 'ENDDOC', 'SUBJECT'])
    issues = result['issues']
    types = {i['issue_type'] for i in issues}
    assert 'missing_required_field' in types
