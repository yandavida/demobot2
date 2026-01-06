from pathlib import Path


def test_no_manual_error_envelope_construction_in_core_validation():
    root = Path("core/validation")
    assert root.exists(), "core/validation directory not found"

    excluded = {"error_envelope.py", "error_taxonomy.py"}
    offenders = []

    for p in sorted(root.glob("*.py")):
        if p.name in excluded:
            continue
        text = p.read_text(encoding="utf8")
        if "ErrorEnvelope(" in text:
            offenders.append(str(p))

    if offenders:
        offender_list = "\n".join(offenders)
        raise AssertionError(
            "Manual ErrorEnvelope(...) construction found in the following files (forbidden).\n"
            "Allowed canonical modules: core/validation/error_envelope.py, core/validation/error_taxonomy.py\n\n"
            f"Offending files:\n{offender_list}"
        )
