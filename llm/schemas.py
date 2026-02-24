"""Output schema definitions and validation for LLM JSON responses."""

import logging

logger = logging.getLogger(__name__)

# ── Schema definitions ─────────────────────────────────────────────────

ESI_ORDER_SCHEMA = {
    'required_keys': ['required_fields', 'hash_required'],
    'types': {
        'required_fields': list,
        'bates_prefix': (str, type(None)),
        'bates_padding': (int, type(None)),
        'valid_confidentiality': list,
        'hash_required': bool,
        'image_format': (str, type(None)),
        'notes': (str, type(None)),
    },
    'list_item_types': {
        'required_fields': str,
        'valid_confidentiality': str,
    },
    'enums': {
        'image_format': ['TIFF', 'PDF', 'native', None],
    },
}

PRIVLOG_SPEC_SCHEMA = {
    'required_keys': ['required_columns', 'categorical_log_allowed'],
    'types': {
        'required_columns': list,
        'date_format': (str, type(None)),
        'sort_order': (str, type(None)),
        'valid_privilege_bases': list,
        'categorical_log_allowed': bool,
        'notes': (str, type(None)),
    },
    'list_item_types': {
        'required_columns': str,
        'valid_privilege_bases': str,
    },
    'enums': {
        'sort_order': ['date', 'bates', 'custodian', None],
    },
}

TERM_CONCEPT_SCHEMA = {
    'required_keys': ['legal_concepts', 'named_entities', 'industry_domain'],
    'types': {
        'legal_concepts': list,
        'named_entities': list,
        'industry_domain': str,
        'custodian_hints': list,
        'custodian_date_ranges': list,
        'notes': (str, type(None)),
    },
    'list_item_types': {
        'legal_concepts': str,
        'named_entities': str,
        'custodian_hints': str,
    },
    'enums': {
        'industry_domain': ['financial_fraud', 'employment', 'ip_theft', 'general'],
    },
}

TERM_DRAFT_ITEM_SCHEMA = {
    'required_keys': ['term_text', 'lucene_equivalent', 'rationale',
                      'risk_notes', 'specialist_flag'],
    'types': {
        'term_text': str,
        'lucene_equivalent': str,
        'rationale': str,
        'risk_notes': str,
        'specialist_flag': bool,
    },
}

FIELD_MAPPING_SCHEMA = {
    'required_keys': [],
    'types': {},           # keys are dynamic (field names)
    'map_sentinel': True,  # all values must be str
}

AI_DATAMAP_SCHEMA = {
    'required_keys': ['company_type', 'data_types', 'notes'],
    'types': {
        'company_type': str,
        'data_types': list,
        'notes': (str, type(None)),
    },
    'list_item_types': {
        'data_types': {
            'required_keys': [
                'category', 'name', 'description',
                'typical_volume', 'typical_format',
                'legal_risk', 'preservation_complexity',
            ],
            'enums': {
                'category': [
                    'training_data', 'model_artifacts', 'api_interactions',
                    'safety_alignment', 'development_records',
                    'email_messaging', 'documents_fileshares',
                    'databases_applications', 'cloud_saas',
                ],
                'legal_risk': ['high', 'medium', 'low'],
                'preservation_complexity': ['high', 'medium', 'low'],
            },
        },
    },
}

AI_HOLD_ANALYSIS_SCHEMA = {
    'required_keys': [
        'scenario_type', 'affected_data_type_ids',
        'hold_scope_summary', 'estimated_volume',
        'suggested_custodians', 'preservation_actions',
        'privilege_considerations', 'cross_border_flags',
    ],
    'types': {
        'scenario_type': str,
        'affected_data_type_ids': list,
        'hold_scope_summary': str,
        'estimated_volume': str,
        'suggested_custodians': list,
        'preservation_actions': list,
        'privilege_considerations': list,
        'cross_border_flags': list,
    },
    'enums': {
        'scenario_type': [
            'copyright_training_data', 'harmful_output', 'antitrust',
            'ip_theft', 'regulatory_inquiry', 'employment_discrimination_ai',
            'contract_dispute', 'data_breach', 'trade_secret',
        ],
    },
}


# ── Validation ─────────────────────────────────────────────────────────

def validate_schema(data, schema: dict, strict: bool = False) -> list[str]:
    """Validate *data* against *schema*. Returns list of error strings (empty = valid).

    When *strict* is True, unexpected keys are also reported.
    For list/array responses, validates each item against the schema.
    """
    # Handle list-of-items (e.g. term_draft returns a JSON array)
    if isinstance(data, list):
        errors: list[str] = []
        for idx, item in enumerate(data):
            for err in validate_schema(item, schema, strict):
                errors.append(f'[{idx}] {err}')
        return errors

    if not isinstance(data, dict):
        return [f'expected dict, got {type(data).__name__}']

    errors = []

    # Map sentinel: every value must be a string
    if schema.get('map_sentinel'):
        for k, v in data.items():
            if not isinstance(v, str):
                errors.append(f'key "{k}": expected str, got {type(v).__name__}')
        return errors

    # Required keys
    for key in schema.get('required_keys', []):
        if key not in data:
            errors.append(f'missing required key: "{key}"')

    # Type checks
    type_spec = schema.get('types', {})
    for key, expected in type_spec.items():
        if key not in data:
            continue
        val = data[key]
        if not isinstance(val, expected):
            nice = (expected.__name__ if isinstance(expected, type)
                    else '|'.join(t.__name__ for t in expected))
            errors.append(
                f'key "{key}": expected {nice}, got {type(val).__name__}'
            )

    # List item types — supports simple types (str, int) or nested schemas (dict)
    for key, item_spec in schema.get('list_item_types', {}).items():
        val = data.get(key)
        if isinstance(val, list):
            if isinstance(item_spec, dict):
                # Nested schema — validate each item as a sub-schema
                for idx, item in enumerate(val):
                    for err in validate_schema(item, item_spec, strict):
                        errors.append(f'key "{key}"[{idx}]: {err}')
            else:
                # Simple type check
                for idx, item in enumerate(val):
                    if not isinstance(item, item_spec):
                        errors.append(
                            f'key "{key}"[{idx}]: expected {item_spec.__name__}, '
                            f'got {type(item).__name__}'
                        )

    # Enum checks
    for key, allowed in schema.get('enums', {}).items():
        if key in data and data[key] not in allowed:
            errors.append(
                f'key "{key}": value {data[key]!r} not in {allowed}'
            )

    # Strict mode — flag unexpected keys
    if strict:
        known = set(type_spec.keys()) | set(schema.get('required_keys', []))
        for key in data:
            if key not in known:
                errors.append(f'unexpected key: "{key}"')

    if errors:
        logger.warning('Schema validation errors: %s', errors)

    return errors
