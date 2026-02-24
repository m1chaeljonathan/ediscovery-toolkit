from modules.ai_lithold import (
    DataType, RiskFlag,
    AI_CATEGORIES, TRADITIONAL_CATEGORIES, CATEGORIES, SCENARIO_TYPES,
    DEFAULT_AI_DATA_TYPES, DEFAULT_TRADITIONAL_DATA_TYPES,
    ALL_DEFAULT_DATA_TYPES,
    compute_risk_flags, compute_gap_analysis,
)


def _make_dt(**overrides):
    """Helper to create a DataType with sensible defaults."""
    defaults = dict(
        id="test_dt", category="training_data", name="Test",
        description="Test data type", typical_volume="1TB",
        typical_format="JSONL", retention_policy="7 years",
        custodian="Data Team", legal_risk="medium",
        preservation_complexity="medium",
    )
    defaults.update(overrides)
    return DataType(**defaults)


def test_default_ai_count():
    assert len(DEFAULT_AI_DATA_TYPES) == 20


def test_default_traditional_count():
    assert len(DEFAULT_TRADITIONAL_DATA_TYPES) == 10


def test_all_defaults_combined():
    assert len(ALL_DEFAULT_DATA_TYPES) == 30


def test_categories_cover_both():
    assert set(AI_CATEGORIES + TRADITIONAL_CATEGORIES) == set(CATEGORIES)


def test_no_flags_when_complete():
    dt = _make_dt(retention_policy="7 years", custodian="Data Team")
    flags = compute_risk_flags([dt])
    assert flags == []


def test_flag_no_retention():
    dt = _make_dt(retention_policy="undefined")
    flags = compute_risk_flags([dt])
    assert any(f.flag_type == "no_retention_policy" for f in flags)


def test_flag_no_custodian():
    dt = _make_dt(custodian="unassigned")
    flags = compute_risk_flags([dt])
    assert any(f.flag_type == "no_custodian" for f in flags)


def test_flag_high_risk_unprotected():
    dt = _make_dt(legal_risk="high", retention_policy="undefined",
                  custodian="unassigned")
    flags = compute_risk_flags([dt])
    assert any(f.flag_type == "high_risk_unprotected" and f.severity == "critical"
               for f in flags)


def test_flag_complex_no_plan():
    dt = _make_dt(preservation_complexity="high", retention_policy="",
                  custodian="Data Team", legal_risk="low")
    flags = compute_risk_flags([dt])
    assert any(f.flag_type == "complex_no_plan" for f in flags)


def test_gap_analysis_empty():
    gap = compute_gap_analysis([])
    assert gap["total_data_types"] == 0
    assert gap["readiness_score"] == 0


def test_gap_analysis_all_defaults():
    gap = compute_gap_analysis(ALL_DEFAULT_DATA_TYPES)
    assert gap["total_data_types"] == 30
    # All defaults have undefined retention and unassigned custodian
    assert gap["no_retention_policy"] == 30
    assert gap["no_custodian"] == 30
    assert gap["readiness_score"] == 0


def test_gap_analysis_perfect_score():
    dt = _make_dt(legal_risk="high", retention_policy="7 years",
                  custodian="Legal Team")
    gap = compute_gap_analysis([dt])
    assert gap["readiness_score"] == 100
    assert gap["no_retention_policy"] == 0
    assert gap["no_custodian"] == 0


def test_gap_missing_categories():
    dt = _make_dt(category="training_data")
    gap = compute_gap_analysis([dt])
    assert "model_artifacts" in gap["missing_categories"]
    assert "training_data" not in gap["missing_categories"]


def test_severity_escalation_high_risk():
    dt = _make_dt(legal_risk="high", retention_policy="undefined",
                  custodian="Data Team")
    flags = compute_risk_flags([dt])
    retention_flag = next(f for f in flags if f.flag_type == "no_retention_policy")
    assert retention_flag.severity == "critical"


def test_severity_normal_risk():
    dt = _make_dt(legal_risk="low", retention_policy="undefined",
                  custodian="Data Team")
    flags = compute_risk_flags([dt])
    retention_flag = next(f for f in flags if f.flag_type == "no_retention_policy")
    assert retention_flag.severity == "high"
