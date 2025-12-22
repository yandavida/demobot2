from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


def _validate_finite(value: float, name: str) -> None:
    if not (value == value and value != float("inf") and value != float("-inf")):
        raise ValueError(f"{name} must be a finite number")


@dataclass(frozen=True)
class Shock:
    spot_pct: float = 0.0
    vol_abs: float = 0.0
    vol_pct: float = 0.0

    def __post_init__(self) -> None:
        _validate_finite(self.spot_pct, "spot_pct")
        _validate_finite(self.vol_abs, "vol_abs")
        _validate_finite(self.vol_pct, "vol_pct")


@dataclass(frozen=True)
class Scenario:
    name: str
    shocks_by_symbol: Tuple[Tuple[str, Shock], ...] = tuple()
    fx_shocks_by_pair: Tuple[Tuple[str, float], ...] = tuple()

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Scenario.name must be non-empty")
        # ensure deterministic ordering of shocks
        sorted_pairs = tuple(sorted(self.shocks_by_symbol, key=lambda kv: str(kv[0])))
        object.__setattr__(self, "shocks_by_symbol", sorted_pairs)
        # validate and normalize fx shocks
        def _validate_pair(pair: str) -> str:
            if "/" not in pair:
                raise ValueError("fx shock pair must be in format 'AAA/BBB'")
            a, b = pair.split("/", 1)
            if not a.isalpha() or not b.isalpha() or not a or not b:
                raise ValueError("fx shock pair must be alphabetic codes like 'USD/ILS'")
            return f"{a.upper()}/{b.upper()}"

        fx_pairs = []
        for pr, mult in self.fx_shocks_by_pair:
            if not (isinstance(mult, (int, float)) and mult > 0.0):
                raise ValueError("fx shock multiplier must be > 0")
            np = _validate_pair(pr)
            fx_pairs.append((np, float(mult)))

        sorted_fx = tuple(sorted(fx_pairs, key=lambda kv: kv[0]))
        object.__setattr__(self, "fx_shocks_by_pair", sorted_fx)


@dataclass(frozen=True)
class ScenarioSet:
    scenarios: Tuple[Scenario, ...] = tuple()

    def __post_init__(self) -> None:
        # sort scenarios deterministically by name
        sorted_sc = tuple(sorted(self.scenarios, key=lambda s: s.name))
        object.__setattr__(self, "scenarios", sorted_sc)


__all__ = ["Shock", "Scenario", "ScenarioSet"]
