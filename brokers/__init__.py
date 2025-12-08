from .sim import SimBroker


def get_broker(name: str = "sim"):
    """מחזיר מופע ברוקר לפי שם."""
    if name == "sim":
        return SimBroker()
    raise ValueError(f"Unknown broker: {name}")
