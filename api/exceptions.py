from __future__ import annotations
from fastapi import HTTPException
from .schemas.errors import ErrorResponse


class ApiException(HTTPException):
    def __init__(
        self, error_type: str, message: str, details=None, status_code: int = 400
    ):
        self.error_type = error_type
        self.details = details or {}
        error_body = ErrorResponse(
            error_type=error_type, message=message, details=self.details
        )
        super().__init__(status_code=status_code, detail=error_body.dict())
