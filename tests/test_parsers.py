from parsers.dat_parser import parse_dat

FIXTURE_DAT = 'tests/fixtures/sample.dat'


def test_dat_parser_row_count():
    result = parse_dat(FIXTURE_DAT)
    assert result.row_count == 2


def test_dat_parser_encoding_detected():
    result = parse_dat(FIXTURE_DAT)
    assert result.encoding_detected == 'utf-8-sig'


def test_dat_parser_begdoc():
    result = parse_dat(FIXTURE_DAT)
    assert result.documents[0].begdoc == 'PROD0000001'


def test_dat_parser_privilege_code():
    result = parse_dat(FIXTURE_DAT)
    assert result.documents[1].privilege_code == 'PRIV'


def test_dat_parser_no_errors():
    result = parse_dat(FIXTURE_DAT)
    assert result.errors == []


def test_dat_parser_headers():
    result = parse_dat(FIXTURE_DAT)
    assert 'BEGDOC' in result.headers
    assert 'CUSTODIAN' in result.headers
