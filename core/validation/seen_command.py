from typing import Any, Tuple

# CommandIdentity: tuple[str, str] = (session_id, command_id)
def has_seen_command(state: Any, identity: Tuple[str, str]) -> bool:
    """
    Returns True if the command identity (session_id, command_id) was seen before in state.
    State is expected to provide a read-only interface:
      state.get_seen_command_ids(session_id) -> set[str]
    """
    session_id, command_id = identity
    seen_ids = set()
    if hasattr(state, "get_seen_command_ids"):
        seen_ids = state.get_seen_command_ids(session_id)
    elif hasattr(state, "seen_command_ids"):
        # fallback for test containers
        seen_ids = state.seen_command_ids.get(session_id, set())
    return command_id in seen_ids
