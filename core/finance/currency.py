<<<<<<< HEAD
# Shim module for backward compatibility; canonical source is core.contracts.money
from core.contracts.money import Currency, normalize_currency
from core.contracts.money import Currency, normalize_currency
=======
<<<<<<< HEAD
from typing import Literal, cast

Currency = Literal["ILS", "USD"]

def normalize_currency(value: Currency | str | None, field_name: str = "currency") -> Currency:
    """
    Normalize an incoming currency value (Literal/str/None) to the Currency
    literal type ("ILS" / "USD"), with validation.
    """
    if value is None:
        raise TypeError(f"{field_name} must not be None")
    if isinstance(value, str):
        normalized = value.upper()
    else:
        normalized = value
    if normalized not in ("ILS", "USD"):
        raise ValueError(f"Unsupported {field_name} {value!r}; expected 'ILS' or 'USD'.")
    return cast(Currency, normalized)
=======
# Shim module for backward compatibility; canonical source is core.contracts.money
from core.contracts.money import Currency, normalize_currency
__all__ = ["Currency", "normalize_currency"]
>>>>>>> ec944a3 (chore(shims): fix finance currency/money shim imports)
>>>>>>> cfe12f6 (chore(shims): fix finance currency/money shim imports)
