# Layer: services
from abc import ABC, abstractmethod


class Broker(ABC):
    """Abstract base interface for broker connections."""

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the broker."""
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the broker."""
        raise NotImplementedError

    def is_connected(self) -> bool:
        """Return connection status."""
        return False
