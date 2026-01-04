from typing import Literal, Optional

Classification = Literal["NEW", "IDEMPOTENT_REPLAY", "CONFLICT"]

def classify_command(seen: bool, previous_fingerprint: Optional[str], current_fingerprint: str) -> Classification:
    if not seen:
        return "NEW"
    if previous_fingerprint == current_fingerprint:
        return "IDEMPOTENT_REPLAY"
    return "CONFLICT"
