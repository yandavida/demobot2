from abc import ABC, abstractmethod
from typing import Any


class Broker(ABC):
    """
    Abstract base interface for broker integrations.

    Minimal, dependency-free contract for connection lifecycle and
    lightweight order/market helpers.
    """

    @abstractmethod
    def connect(self) -> None:
        \"\"\"Establish connection to the broker.\"\"\"
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        \"\"\"Tear down connection and release resources.\"\"\"
        raise NotImplementedError

    @abstractmethod
    def is_connected(self) -> bool:
        \"\"\"Return True when the broker connection is active.\"\"\"
        raise NotImplementedError

    # Optional helpers for later (no concrete trading logic here).
    def get_price(self, symbol: str) -> float | None:
        \"\"\"Return latest price for symbol or None if unavailable.\"\"\"
        return None

    def preview_order(self, *args: Any, **kwargs: Any) -> Any:
        \"\"\"Return a lightweight preview of the order (fees, fills, etc.).\"\"\"
        raise NotImplementedError

    def place_order(self, *args: Any, **kwargs: Any) -> Any:
        \"\"\"Place an order; return broker-specific order handle/response.\"\"\"
        raise NotImplementedError
