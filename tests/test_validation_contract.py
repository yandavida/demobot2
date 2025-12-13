from core.quote_validation import ValidationSummary


def test_validation_summary_to_dict_key_order_and_counts() -> None:
    summary = ValidationSummary(max_items=5)
    summary.add_error("err-1")
    summary.add_warning("warn-1")

    payload = summary.to_dict()

    assert list(payload.keys()) == ["errors", "warnings", "error_count", "warning_count"]
    assert payload["errors"] == ["err-1"]
    assert payload["warnings"] == ["warn-1"]
    assert payload["error_count"] == 1
    assert payload["warning_count"] == 1


def test_validation_summary_to_dict_caps_lists_but_preserves_counters() -> None:
    summary = ValidationSummary(max_items=3)
    for i in range(5):
        summary.add_error(f"err-{i}")
    for i in range(4):
        summary.add_warning(f"warn-{i}")

    payload = summary.to_dict()

    assert len(payload["errors"]) == 3
    assert payload["errors"] == ["err-0", "err-1", "err-2"]
    assert payload["warnings"] == ["warn-0", "warn-1", "warn-2"]
    assert payload["error_count"] == 5
    assert payload["warning_count"] == 4
