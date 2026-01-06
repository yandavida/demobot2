from core.validation.validation_modes import (
    ValidationMode,
    apply_validation_mode,
    DOWNGRADEABLE_SEMANTIC_CODES,
)
from core.validation.operational_outcome import ErrorEnvelope


def mk(code: str, category: str) -> ErrorEnvelope:
    # Build an ErrorEnvelope directly so tests can control category and code
    return ErrorEnvelope(category=category, code=code, message=code, details={"path": "x"}, error_count=1)


def test_strict_rejects_all_categories():
    errs = [mk("E1", "VALIDATION"), mk("E2", "SEMANTIC"), mk("E3", "CONFLICT")]
    dec = apply_validation_mode(ValidationMode.STRICT, errs)
    assert dec.accepted is False
    assert len(dec.errors) == 3
    assert dec.warnings == []


def test_lenient_rejects_validation_and_conflict():
    errs = [mk("V1", "VALIDATION"), mk("C1", "CONFLICT")]
    dec = apply_validation_mode(ValidationMode.LENIENT, errs)
    assert dec.accepted is False
    # both errors remain
    codes = {e.code for e in dec.errors}
    assert "V1" in codes and "C1" in codes


def test_lenient_semantic_default_rejects():
    errs = [mk("S1", "SEMANTIC")]
    dec = apply_validation_mode(ValidationMode.LENIENT, errs)
    assert dec.accepted is False
    assert dec.errors[0].code == "S1"


def test_lenient_can_downgrade_allowlisted_semantic(monkeypatch):
    # Temporarily set allowlist
    monkeypatch.setattr(
        "core.validation.validation_modes.DOWNGRADEABLE_SEMANTIC_CODES",
        {"S_OK"},
        raising=False,
    )
    errs = [mk("S_OK", "SEMANTIC")]
    dec = apply_validation_mode(ValidationMode.LENIENT, errs)
    assert dec.accepted is True
    assert dec.errors == []
    assert len(dec.warnings) == 1
    assert dec.warnings[0].code == "S_OK"


def test_deterministic_precedence_warning_and_validation():
    # a downgradeable semantic together with a validation error => reject
    errs = [mk("S_OK", "SEMANTIC"), mk("V_FAIL", "VALIDATION")]
    # ensure allowlist contains S_OK
    orig = DOWNGRADEABLE_SEMANTIC_CODES.copy()
    try:
        DOWNGRADEABLE_SEMANTIC_CODES.clear()
        DOWNGRADEABLE_SEMANTIC_CODES.add("S_OK")
        dec = apply_validation_mode(ValidationMode.LENIENT, errs)
        assert dec.accepted is False
        codes = {e.code for e in dec.errors}
        assert "V_FAIL" in codes
    finally:
        DOWNGRADEABLE_SEMANTIC_CODES.clear()
        DOWNGRADEABLE_SEMANTIC_CODES.update(orig)
