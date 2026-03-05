from __future__ import annotations

import pytest

from core.portfolio.portfolio_ref_resolver_v1 import PortfolioResolutionError
from core.portfolio.portfolio_ref_resolver_v1 import resolve_portfolio_ref_to_advisory_payload_v1


def test_portfolio_ref_resolver_is_deterministic_hard_failure_without_source() -> None:
    with pytest.raises(PortfolioResolutionError, match="no_portfolio_source_registered"):
        resolve_portfolio_ref_to_advisory_payload_v1("portfolio-1")


def test_invalid_portfolio_ref_raises() -> None:
    with pytest.raises(PortfolioResolutionError, match="invalid_portfolio_ref"):
        resolve_portfolio_ref_to_advisory_payload_v1("   ")
