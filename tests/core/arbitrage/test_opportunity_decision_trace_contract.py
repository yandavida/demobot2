import pytest
import json
from core.arbitrage.opportunity_views.reasons import Reason, ReasonCode
from core.arbitrage.opportunity_views.metrics import MetricValue
from core.arbitrage.opportunity_views.decision_trace import OpportunityDecisionTrace

def test_rejected_must_have_reasons():
    with pytest.raises(ValueError):
        OpportunityDecisionTrace(
            candidate_id="c1",
            accepted=False,
            reasons=(),
            metrics=(),
            pareto={},
            tie_break_key="c1"
        )

def test_accepted_must_not_have_reject_reasons():
    reason = Reason(
        code=ReasonCode.MIN_EDGE_NOT_MET,
        message="Edge below threshold"
    )
    with pytest.raises(ValueError):
        OpportunityDecisionTrace(
            candidate_id="c2",
            accepted=True,
            reasons=(reason,),
            metrics=(),
            pareto={},
            tie_break_key="c2"
        )

def test_duplicate_metric_names_forbidden():
    m1 = MetricValue(name="edge", value=1.0, unit="bps", direction="max")
    m2 = MetricValue(name="edge", value=2.0, unit="bps", direction="max")
    reason = Reason(code=ReasonCode.INVALID_QUOTES, message="Invalid quotes")
    with pytest.raises(ValueError):
        OpportunityDecisionTrace(
            candidate_id="c3",
            accepted=False,
            reasons=(reason,),
            metrics=(m1, m2),
            pareto={},
            tie_break_key="c3"
        )

def test_json_serializability():
    reason = Reason(code=ReasonCode.STALE_QUOTES, message="Quotes are stale", observed=1.0, threshold=2.0, unit="s", context={"age": "1.0"})
    metric = MetricValue(name="edge", value=1.5, unit="bps", direction="max")
    trace = OpportunityDecisionTrace(
        candidate_id="c4",
        accepted=False,
        reasons=(reason,),
        metrics=(metric,),
        pareto={"is_pareto_optimal": True, "dominated_by": None, "pareto_rank": 1, "tie_break_key": "c4"},
        tie_break_key="c4"
    )
    d = trace.to_dict()
    # Should be JSON-safe
    json_str = json.dumps(d)
    assert isinstance(json_str, str)
    # Only JSON-safe types
    def is_json_safe(val):
        return isinstance(val, (str, float, int, bool, type(None), dict, list))
    def check_types(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                check_types(v)
        elif isinstance(obj, (list, tuple)):
            for v in obj:
                check_types(v)
        else:
            assert is_json_safe(obj)
    check_types(d)

def test_tie_break_key_determinism():
    reason = Reason(code=ReasonCode.MISSING_QUOTES, message="Missing quotes")
    metric = MetricValue(name="edge", value=2.0, unit="bps", direction="max")
    t1 = OpportunityDecisionTrace(
        candidate_id="c5",
        accepted=False,
        reasons=(reason,),
        metrics=(metric,),
        pareto={"pareto_rank": 1},
        tie_break_key="c5"
    )
    t2 = OpportunityDecisionTrace(
        candidate_id="c6",
        accepted=False,
        reasons=(reason,),
        metrics=(metric,),
        pareto={"pareto_rank": 2},
        tie_break_key="c6"
    )
    traces = [t2, t1]
    traces_sorted = sorted(traces, key=lambda tr: (tr.pareto.get("pareto_rank", 0), tr.tie_break_key))
    assert traces_sorted[0].candidate_id == "c5"
    assert traces_sorted[1].candidate_id == "c6"
