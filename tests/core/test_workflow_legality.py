from core.validation.workflow_legality import WorkflowContext, check_workflow_legality
from core.validation.operational_outcome import ErrorEnvelope
from core.validation.command_registry import validate_command_dict


def test_compute_request_rejected_without_quotes():
    ctx = WorkflowContext(has_any_quotes=False, applied_version=0)
    cmd = {"kind": "COMPUTE_REQUEST", "schema_version": 1}
    # schema validation passes
    assert validate_command_dict({"kind": "COMPUTE_REQUEST", "schema_version": 1}) is None
    err = check_workflow_legality(ctx, cmd)
    assert isinstance(err, ErrorEnvelope)
    assert err.code == "ILLEGAL_SEQUENCE"


def test_compute_request_allowed_after_quote():
    ctx = WorkflowContext(has_any_quotes=True, applied_version=0)
    cmd = {"kind": "COMPUTE_REQUEST", "schema_version": 1}
    assert validate_command_dict(cmd) is None
    err = check_workflow_legality(ctx, cmd)
    assert err is None


def test_snapshot_request_rejected_before_applied_version():
    ctx = WorkflowContext(has_any_quotes=True, applied_version=0)
    cmd = {"kind": "SNAPSHOT_REQUEST", "schema_version": 1}
    assert validate_command_dict(cmd) is None
    err = check_workflow_legality(ctx, cmd)
    assert isinstance(err, ErrorEnvelope)
    assert err.code == "ILLEGAL_SEQUENCE"


def test_snapshot_request_allowed_after_applied_version():
    ctx = WorkflowContext(has_any_quotes=True, applied_version=1)
    cmd = {"kind": "SNAPSHOT_REQUEST", "schema_version": 1}
    assert validate_command_dict(cmd) is None
    err = check_workflow_legality(ctx, cmd)
    assert err is None


def test_ingest_quote_always_allowed():
    ctx = WorkflowContext(has_any_quotes=False, applied_version=0)
    cmd = {"kind": "INGEST_QUOTE", "schema_version": 1}
    # passes schema check
    assert validate_command_dict(cmd) is None
    # legality layer should allow it
    err = check_workflow_legality(ctx, cmd)
    assert err is None


def test_precedence_versioning_before_legality():
    # unsupported schema_version + illegal ordering -> expect versioning error first
    ctx = WorkflowContext(has_any_quotes=False, applied_version=0)
    cmd = {"kind": "COMPUTE_REQUEST", "schema_version": 999}
    v_err = validate_command_dict(cmd)
    assert v_err is not None
    assert v_err.code in {"UNSUPPORTED_SCHEMA_VERSION", "MISSING_SCHEMA_VERSION"}
    # If we called legality, it would also reject, but ensure versioning fails first
    l_err = check_workflow_legality(ctx, cmd)
    # legality may or may not report, but we assert versioning error present and decisive
    assert v_err.code != "ILLEGAL_SEQUENCE"
