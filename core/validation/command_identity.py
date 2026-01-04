from typing import Tuple, Any

def get_command_identity(cmd: Any) -> Tuple[str, str]:
    """
    Canonical idempotency identity for Gate B:
    (session_id, command_id)
    """
    # Always return str, never None
    session_id = getattr(cmd, "session_id", "")
    command_id = getattr(cmd, "command_id", "")
    return (str(session_id), str(command_id))

# Type alias for clarity
CommandIdentity = Tuple[str, str]
