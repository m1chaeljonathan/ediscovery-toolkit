from modules.term_generator.name_proximity import (
    _is_person_name,
    generate_name_terms,
    NICKNAMES,
)


def test_person_name_two_words():
    assert _is_person_name("David Smith") is True


def test_person_name_three_words():
    assert _is_person_name("Mary Jane Watson") is True


def test_rejects_single_word():
    assert _is_person_name("David") is False


def test_rejects_four_words():
    assert _is_person_name("Sir David Alan Smith") is False


def test_rejects_corporate_suffix():
    assert _is_person_name("Acme Corp") is False
    assert _is_person_name("Smith Holdings") is False
    assert _is_person_name("Jones LLC") is False


def test_rejects_lowercase_words():
    assert _is_person_name("david smith") is False


def test_nickname_lookup():
    assert "bob" in NICKNAMES["robert"]
    assert "rob" in NICKNAMES["robert"]
    assert "mike" in NICKNAMES["michael"]


def test_generate_canonical_term():
    terms = generate_name_terms(["David Smith"])
    canonical = terms[0]
    assert canonical["term_text"] == "david W/3 smith"
    assert canonical["lucene_equivalent"] == '"david smith"~3'
    assert "David Smith" in canonical["rationale"]


def test_generate_nickname_variation():
    terms = generate_name_terms(["Robert Jones"])
    texts = [t["term_text"] for t in terms]
    assert "robert W/3 jones" in texts
    assert "bob W/3 jones" in texts
    assert "rob W/3 jones" in texts


def test_company_excluded_from_generation():
    terms = generate_name_terms(["Acme Corp", "Robert Jones"])
    texts = [t["term_text"] for t in terms]
    assert not any("acme" in t for t in texts)
    assert "robert W/3 jones" in texts


def test_mixed_entity_list():
    entities = ["John Smith", "Enron Corp", "Mary Jane Watson"]
    terms = generate_name_terms(entities)
    texts = [t["term_text"] for t in terms]
    assert "john W/3 smith" in texts
    # Three-word name: first W/3 last
    assert "mary W/3 watson" in texts
    assert not any("enron" in t for t in texts)


def test_lucene_format():
    terms = generate_name_terms(["Michael Chen"])
    for t in terms:
        assert t["lucene_equivalent"].startswith('"')
        assert t["lucene_equivalent"].endswith('~3')


def test_no_person_names_returns_empty():
    assert generate_name_terms([]) == []
    assert generate_name_terms(["Acme Inc", "Beta LLC"]) == []
