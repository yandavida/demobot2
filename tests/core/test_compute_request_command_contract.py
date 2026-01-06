import pytest
from dataclasses import FrozenInstanceError

from core.commands.compute_request_command import (
    ComputeRequestPayload,
    ComputeRequestCommand,
)


def test_defaults_and_shape():
    payload = ComputeRequestPayload(kind="SNAPSHOT", params={})
    assert payload.params == {}

    cmd = ComputeRequestCommand(command_id="c1", session_id="s1", payload=payload)
    assert cmd.strict is True
    assert cmd.meta is None
    assert cmd.kind == "COMPUTE_REQUEST"


def test_immutability_and_params_is_fresh():
    p1 = ComputeRequestPayload(kind="SNAPSHOT")
    p2 = ComputeRequestPayload(kind="SNAPSHOT")
    assert p1.params is not p2.params

    cmd = ComputeRequestCommand(command_id="c2", session_id="s2", payload=p1)
    with pytest.raises(FrozenInstanceError):
        cmd.strict = False


def test_payload_required_and_kind_literal():
    payload = ComputeRequestPayload(kind="PORTFOLIO_RISK")
    cmd = ComputeRequestCommand(command_id="id", session_id="sid", payload=payload)
    assert isinstance(cmd.payload, ComputeRequestPayload)
