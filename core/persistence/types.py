"""
Typed exceptions for storage layer.
"""
class StorageError(Exception):
    """Base exception for storage errors."""
    pass

class StorageIntegrityError(StorageError):
    """Raised on integrity constraint violations (e.g., duplicate event_id)."""
    pass

class StorageConnectionError(StorageError):
    """Raised on connection or DB availability errors."""
    pass
