from modules.term_analytics import validate_syntax, compute_stats


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


def test_zero_hits_flag():
    """ZERO HITS only fires when other terms have hit data (not on fresh terms)."""
    s = compute_stats([
        {'term_text': 'x', 'syntax': 'dtsearch',
         'doc_hits': 0, 'family_hits': 0, 'unique_hits': 0},
        {'term_text': 'y', 'syntax': 'dtsearch',
         'doc_hits': 100, 'family_hits': 100, 'unique_hits': 80},
    ], 1000)
    assert 'ZERO HITS' in s[0].risk_flags
    assert 'ZERO HITS' not in s[1].risk_flags


def test_zero_hits_suppressed_when_no_data():
    """All terms at 0 hits means no hit data entered yet — don't flag."""
    s = compute_stats([{'term_text': 'x', 'syntax': 'dtsearch',
                        'doc_hits': 0, 'family_hits': 0, 'unique_hits': 0}], 1000)
    assert 'ZERO HITS' not in s[0].risk_flags


def test_over_broad_flag():
    s = compute_stats([{'term_text': 'x', 'syntax': 'dtsearch',
                        'doc_hits': 900, 'family_hits': 900, 'unique_hits': 900}], 1000)
    assert 'OVER-BROAD' in s[0].risk_flags


def test_clean_term():
    s = compute_stats([{'term_text': 'fraud~ W/10 payment', 'syntax': 'dtsearch',
                        'doc_hits': 50, 'family_hits': 60, 'unique_hits': 45}], 1000)
    assert s[0].risk_flags == []
