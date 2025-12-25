"""Shim module for backward compatibility.

Canonical source of truth: core.contracts.money
"""

from core.contracts.money import Currency, normalize_currency

__all__ = ["Currency", "normalize_currency"]
 
