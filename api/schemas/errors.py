from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, Dict, Any


class ErrorResponse(BaseModel):
    error_type: str  # "VALIDATION", "SERVER", "NETWORK", ...
    message: str  # הודעה ידידותית
    details: Optional[Dict[str, Any]] = None
