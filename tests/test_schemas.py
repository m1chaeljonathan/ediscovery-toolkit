"""Tests for llm.schemas — output schema validation."""

from llm.schemas import (
    validate_schema,
    ESI_ORDER_SCHEMA,
    PRIVLOG_SPEC_SCHEMA,
    TERM_CONCEPT_SCHEMA,
    TERM_DRAFT_ITEM_SCHEMA,
    FIELD_MAPPING_SCHEMA,
)


# ── Valid data passes all schemas ──────────────────────────────────────

def test_valid_esi_order():
    data = {
        'required_fields': ['BEGDOC', 'ENDDOC', 'CUSTODIAN'],
        'bates_prefix': 'PROD',
        'bates_padding': 7,
        'valid_confidentiality': ['CONFIDENTIAL'],
        'hash_required': True,
        'image_format': 'TIFF',
        'notes': None,
    }
    assert validate_schema(data, ESI_ORDER_SCHEMA) == []


def test_valid_privlog_spec():
    data = {
        'required_columns': ['Date', 'Author', 'Description'],
        'date_format': 'MM/DD/YYYY',
        'sort_order': 'bates',
        'valid_privilege_bases': ['Attorney-Client', 'Work Product'],
        'categorical_log_allowed': False,
        'notes': None,
    }
    assert validate_schema(data, PRIVLOG_SPEC_SCHEMA) == []


def test_valid_term_concept():
    data = {
        'legal_concepts': ['fraud', 'breach of contract'],
        'named_entities': ['John Smith', 'Acme Corp'],
        'industry_domain': 'financial_fraud',
        'custodian_hints': ['John Smith'],
        'custodian_date_ranges': [],
        'notes': 'Relevant period 2020-2023',
    }
    assert validate_schema(data, TERM_CONCEPT_SCHEMA) == []


def test_valid_term_draft_item():
    data = {
        'term_text': 'fraud~ W/10 payment',
        'lucene_equivalent': '"fraud payment"~10',
        'rationale': 'Targets fraud near payment terms',
        'risk_notes': 'May catch legitimate payment discussions',
        'specialist_flag': False,
    }
    assert validate_schema(data, TERM_DRAFT_ITEM_SCHEMA) == []


def test_valid_field_mapping():
    data = {
        'Item ID': 'BEGDOC',
        'Custodian Name': 'CUSTODIAN',
    }
    assert validate_schema(data, FIELD_MAPPING_SCHEMA) == []


# ── Missing required keys ─────────────────────────────────────────────

def test_missing_required_fields():
    data = {'bates_prefix': 'PROD'}  # missing required_fields and hash_required
    errors = validate_schema(data, ESI_ORDER_SCHEMA)
    assert any('"required_fields"' in e for e in errors)
    assert any('"hash_required"' in e for e in errors)


def test_missing_term_concept_required():
    data = {'notes': 'only notes'}
    errors = validate_schema(data, TERM_CONCEPT_SCHEMA)
    assert any('"legal_concepts"' in e for e in errors)
    assert any('"industry_domain"' in e for e in errors)


# ── Wrong types ────────────────────────────────────────────────────────

def test_wrong_type_string_for_list():
    data = {
        'required_fields': 'BEGDOC',  # should be list
        'hash_required': True,
    }
    errors = validate_schema(data, ESI_ORDER_SCHEMA)
    assert any('"required_fields"' in e and 'list' in e for e in errors)


def test_wrong_type_string_for_bool():
    data = {
        'required_fields': ['BEGDOC'],
        'hash_required': 'yes',  # should be bool
    }
    errors = validate_schema(data, ESI_ORDER_SCHEMA)
    assert any('"hash_required"' in e and 'bool' in e for e in errors)


def test_wrong_type_in_field_mapping():
    data = {'Item ID': 123}  # value should be str
    errors = validate_schema(data, FIELD_MAPPING_SCHEMA)
    assert any('"Item ID"' in e for e in errors)


# ── Null violations ────────────────────────────────────────────────────

def test_null_not_allowed_for_required_fields_list():
    data = {
        'required_fields': None,  # list, not nullable
        'hash_required': True,
    }
    errors = validate_schema(data, ESI_ORDER_SCHEMA)
    assert any('"required_fields"' in e for e in errors)


def test_null_allowed_for_bates_prefix():
    data = {
        'required_fields': ['BEGDOC'],
        'bates_prefix': None,
        'hash_required': True,
    }
    errors = validate_schema(data, ESI_ORDER_SCHEMA)
    assert errors == []


# ── Enum violations ────────────────────────────────────────────────────

def test_invalid_image_format():
    data = {
        'required_fields': ['BEGDOC'],
        'hash_required': True,
        'image_format': 'JPEG',  # not in enum
    }
    errors = validate_schema(data, ESI_ORDER_SCHEMA)
    assert any('"image_format"' in e and 'JPEG' in e for e in errors)


def test_invalid_industry_domain():
    data = {
        'legal_concepts': ['fraud'],
        'named_entities': [],
        'industry_domain': 'healthcare',  # not in enum
    }
    errors = validate_schema(data, TERM_CONCEPT_SCHEMA)
    assert any('"industry_domain"' in e for e in errors)


def test_invalid_sort_order():
    data = {
        'required_columns': ['Date'],
        'categorical_log_allowed': True,
        'sort_order': 'alphabetical',  # not in enum
        'valid_privilege_bases': [],
    }
    errors = validate_schema(data, PRIVLOG_SPEC_SCHEMA)
    assert any('"sort_order"' in e for e in errors)


# ── List item type validation ──────────────────────────────────────────

def test_list_items_wrong_type():
    data = {
        'required_fields': ['BEGDOC', 123, 'CUSTODIAN'],  # 123 is not str
        'hash_required': True,
    }
    errors = validate_schema(data, ESI_ORDER_SCHEMA)
    assert any('"required_fields"[1]' in e for e in errors)


# ── Strict mode — unexpected keys ─────────────────────────────────────

def test_strict_flags_unexpected_key():
    data = {
        'term_text': 'fraud',
        'lucene_equivalent': '"fraud"',
        'rationale': 'test',
        'risk_notes': 'none',
        'specialist_flag': False,
        'extra_field': 'should not be here',
    }
    errors = validate_schema(data, TERM_DRAFT_ITEM_SCHEMA, strict=True)
    assert any('"extra_field"' in e for e in errors)


def test_non_strict_allows_extra_key():
    data = {
        'term_text': 'fraud',
        'lucene_equivalent': '"fraud"',
        'rationale': 'test',
        'risk_notes': 'none',
        'specialist_flag': False,
        'extra_field': 'allowed',
    }
    errors = validate_schema(data, TERM_DRAFT_ITEM_SCHEMA, strict=False)
    assert errors == []


# ── Array validation (list of term draft items) ───────────────────────

def test_array_of_valid_items():
    items = [
        {
            'term_text': 'fraud~ W/10 payment',
            'lucene_equivalent': '"fraud payment"~10',
            'rationale': 'target fraud',
            'risk_notes': 'broad',
            'specialist_flag': False,
        },
        {
            'term_text': 'terminat~ W/5 employ~',
            'lucene_equivalent': '"terminate employ"~5',
            'rationale': 'wrongful termination',
            'risk_notes': 'HR context',
            'specialist_flag': True,
        },
    ]
    assert validate_schema(items, TERM_DRAFT_ITEM_SCHEMA) == []


def test_array_with_invalid_item():
    items = [
        {
            'term_text': 'fraud',
            'lucene_equivalent': '"fraud"',
            'rationale': 'test',
            'risk_notes': 'none',
            'specialist_flag': False,
        },
        {
            'term_text': 'bad item',
            # missing required keys
        },
    ]
    errors = validate_schema(items, TERM_DRAFT_ITEM_SCHEMA)
    assert any('[1]' in e for e in errors)
    assert not any('[0]' in e for e in errors)


# ── Non-dict input ─────────────────────────────────────────────────────

def test_non_dict_non_list_input():
    errors = validate_schema("just a string", ESI_ORDER_SCHEMA)
    assert any('expected dict' in e for e in errors)
