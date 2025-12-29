from api.v2.portfolio_schemas import PortfolioSummaryOut, MoneyOut, ExposureOut, ConstraintsOut
from api.v2.service import get_v2_service
from core.portfolio.v2_reducer import reduce_portfolio_state
from core.portfolio.v2_aggregation import aggregate_portfolio
from core.portfolio.v2_constraints import evaluate_constraints
from fastapi import HTTPException

def get_portfolio_summary(session_id: str) -> PortfolioSummaryOut:
    # Load events from EventStore
    svc = get_v2_service()
    events = svc.event_store.list(session_id)
    if not events:
        raise HTTPException(status_code=404, detail="Session not found")
    snapshot = svc.snapshot_store.latest(session_id)
    version = snapshot.version if snapshot else len(events)
    import logging
    logger = logging.getLogger("demobot.v2")
    try:
        state = reduce_portfolio_state(events)
        if state is None:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        totals = aggregate_portfolio(state)
        constraints_report = evaluate_constraints(state, totals)
        exposures = [
            ExposureOut(
                underlying=u,
                abs_notional=ex.abs_notional,
                delta=ex.delta,
            ) for u, ex in totals.exposures
        ]
        return PortfolioSummaryOut(
            session_id=session_id,
            version=version,
            pv=MoneyOut(value=totals.pv, currency=state.base_currency),
            delta=totals.greeks.delta,
            exposures=exposures,
            constraints=ConstraintsOut(
                passed=constraints_report.passed,
                breaches=[b.message for b in constraints_report.breaches],
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"detail": str(exc)}) from exc
    except Exception as exc:
        logger.exception("portfolio.summary failed", extra={"session_id": session_id})
        raise
