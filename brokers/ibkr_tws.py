# Layer: services
from ib_insync import IB

from brokers.base import Broker


class IBKRTWS(Broker):
    """Interactive Brokers TWS connector (skeleton)."""

    def __init__(self):
        self.ib = IB()
        self.connected = False

    def connect(self) -> None:
        """Connect to IBKR TWS or Gateway."""
        try:
            self.ib.connect("127.0.0.1", 7497, clientId=1)
            self.connected = True
        except Exception as e:
            print(f"Connection failed: {e}")
            self.connected = False

    def disconnect(self) -> None:
        """Disconnect from IBKR TWS."""
        self.ib.disconnect()
        self.connected = False

    def is_connected(self) -> bool:
        return self.connected
