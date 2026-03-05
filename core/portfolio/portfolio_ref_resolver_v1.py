from __future__ import annotations


class PortfolioResolutionError(ValueError):
    pass


def resolve_portfolio_ref_to_advisory_payload_v1(portfolio_ref: str) -> dict:
    if not isinstance(portfolio_ref, str) or not portfolio_ref.strip():
        raise PortfolioResolutionError("invalid_portfolio_ref")

    # No canonical SSOT source exists yet for mapping portfolio_ref -> advisory payload.
    raise PortfolioResolutionError("no_portfolio_source_registered")


__all__ = [
    "PortfolioResolutionError",
    "resolve_portfolio_ref_to_advisory_payload_v1",
]
