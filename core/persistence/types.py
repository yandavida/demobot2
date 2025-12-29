"""
Persistence error contract for V2 stores.
"""

class StorageError(Exception):
    """Base error for persistence layer."""
    pass

class StorageIntegrityError(StorageError):
    """Raised on integrity violations (e.g. duplicate, conflict)."""
    pass

class StorageConnectionError(StorageError):
    """Raised on connection or migration failures."""
    pass
