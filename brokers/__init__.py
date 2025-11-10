# brokers/__init__.py
# -------------------
from . import sim


def get_broker(name: str):
    """
    פונקציה שמחזירה 'ברוקר' לפי שם.
    כרגע רק סימולטור פעיל.
    """
    if name == "sim":
        # נחזיר מודול עם פונקציות סטנדרטיות (simulate)
        return sim
    else:
        raise ValueError(f"Unknown broker name: {name}")
