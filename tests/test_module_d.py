from modules.term_analytics import validate_syntax, compute_stats, group_date_ranges


def test_unbalanced_parens():
    assert any('parenthes' in e.lower()
               for e in validate_syntax('(fraud AND payment'))


def test_missing_proximity():
    assert any('proximity' in e.lower()
               for e in validate_syntax('fraud W/ payment'))


def test_leading_wildcard():
    assert any('wildcard' in e.lower()
               for e in validate_syntax('*smith AND jones'))


def test_lowercase_boolean():
    assert any('uppercase' in e.lower()
               for e in validate_syntax('fraud and payment', 'dtsearch'))


def test_valid_term():
    assert validate_syntax('fraud~ W/10 payment AND transfer~') == []


def test_over_broad_flag():
    s = compute_stats([{'term_text': 'x', 'syntax': 'dtsearch',
                        'doc_hits': 900, 'family_hits': 900, 'unique_hits': 900}], 1000)
    assert 'OVER-BROAD' in s[0].risk_flags


def test_clean_term():
    s = compute_stats([{'term_text': 'fraud~ W/10 payment', 'syntax': 'dtsearch',
                        'doc_hits': 50, 'family_hits': 60, 'unique_hits': 45}], 1000)
    assert s[0].risk_flags == []


def test_group_date_ranges():
    ranges = [
        {"custodian": "Alice", "start_date": "2020-01-01", "end_date": "2023-06-30", "source": "employment"},
        {"custodian": "Bob", "start_date": "2020-01-01", "end_date": "2023-06-30", "source": "employment"},
        {"custodian": "Carol", "start_date": "2021-03-15", "end_date": "2023-12-31", "source": "contract"},
    ]
    grouped = group_date_ranges(ranges)
    assert ("2020-01-01", "2023-06-30") in grouped
    assert grouped[("2020-01-01", "2023-06-30")] == ["Alice", "Bob"]
    assert grouped[("2021-03-15", "2023-12-31")] == ["Carol"]


def test_group_date_ranges_empty():
    assert group_date_ranges([]) == {}
