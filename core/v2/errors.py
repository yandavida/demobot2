class EventConflictError(Exception):
    def __init__(self, session_id: str, event_id: str, existing_type: str, incoming_type: str, existing_hash: str, incoming_hash: str):
        self.session_id = session_id
        self.event_id = event_id
        self.existing_type = existing_type
        self.incoming_type = incoming_type
        self.existing_hash = existing_hash
        self.incoming_hash = incoming_hash
        super().__init__(
            f"Event conflict for session_id={session_id} event_id={event_id} "
            f"(existing_type={existing_type}, incoming_type={incoming_type}, "
            f"existing_hash={existing_hash}, incoming_hash={incoming_hash})"
        )
