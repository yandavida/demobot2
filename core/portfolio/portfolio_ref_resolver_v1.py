from __future__ import annotations

from core.portfolio.advisory_payload_artifact_store_v1 import AdvisoryPayloadArtifactNotFoundError
from core.portfolio.advisory_payload_artifact_store_v1 import get_advisory_payload_artifact_v1
from core.services.advisory_input_contract_v1 import normalize_advisory_input_v1
from core.v2.snapshot_store_sqlite import SqliteSnapshotStore


class PortfolioResolutionError(ValueError):
    pass


def resolve_portfolio_ref_to_advisory_payload_v1(portfolio_ref: str) -> dict:
    if not isinstance(portfolio_ref, str) or not portfolio_ref.strip():
        raise PortfolioResolutionError("invalid_portfolio_ref")

    ref = portfolio_ref.strip()
    if ref.startswith("inline:"):
        raise PortfolioResolutionError("unsupported_portfolio_ref_format")

    if ref.startswith("artifact:"):
        artifact_id = ref.split(":", 1)[1].strip()
        if not artifact_id:
            raise PortfolioResolutionError("unsupported_portfolio_ref_format")
        try:
            payload = get_advisory_payload_artifact_v1(artifact_id)
        except AdvisoryPayloadArtifactNotFoundError as exc:
            raise PortfolioResolutionError(f"portfolio_artifact_not_found:{artifact_id}") from exc
        except Exception as exc:
            raise PortfolioResolutionError(f"portfolio_artifact_invalid:{artifact_id}") from exc

        normalize_advisory_input_v1(payload)
        return payload

    if ref.startswith("portfolio:"):
        portfolio_id = ref.split(":", 1)[1].strip()
        if not portfolio_id:
            raise PortfolioResolutionError("unsupported_portfolio_ref_format")

        snapshot = SqliteSnapshotStore().get_latest(portfolio_id)
        if snapshot is None:
            raise PortfolioResolutionError(f"portfolio_snapshot_not_found:{portfolio_id}")

        payload = snapshot.data if isinstance(snapshot.data, dict) else {}
        try:
            normalize_advisory_input_v1(payload)
        except Exception as exc:
            raise PortfolioResolutionError(f"portfolio_snapshot_not_advisory_payload:{portfolio_id}") from exc
        return payload

    raise PortfolioResolutionError("unsupported_portfolio_ref_format")


__all__ = [
    "PortfolioResolutionError",
    "resolve_portfolio_ref_to_advisory_payload_v1",
]
