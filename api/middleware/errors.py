from __future__ import annotations
from fastapi import Request
import os
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from api.exceptions import ApiException
from api.schemas.errors import ErrorResponse


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)

        except ApiException as e:
            return JSONResponse(
                status_code=e.status_code,
                content=ErrorResponse(
                    error_type=e.error_type,
                    message=e.detail["message"],
                    details=e.detail.get("details", {}),
                ).dict(),
            )

        except Exception as e:
            if "PYTEST_CURRENT_TEST" in os.environ:
                raise
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    error_type="SERVER",
                    message="Internal server error",
                    details={"raw": str(e)},
                ).dict(),
            )
