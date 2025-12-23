from __future__ import annotations

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response as StarletteResponse

from api.logging_config import configure_logging
from api.routers.fx_router import router as fx_router
from api.routers.portfolio_router import router as portfolio_router
from api.routers.strategy_router import router as strategy_router
from api.v1 import arbitrage_orch
from api.v2.router import router as v2_router
from api.middleware.errors import ErrorHandlingMiddleware
from api.v2.correlation import CORRELATION_ID_HEADER, get_or_create_correlation_id

# להגדיר לוגים לפני יצירת האפליקציה
configure_logging()

app = FastAPI(
    title="DemoBot SaaS API",
    version="0.1.0",
)

# Middleware להבטחת X-Correlation-Id בכל /api/v2, כולל 500
class V2CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next) -> StarletteResponse:
        # Non-V2: do not touch anything (preserve v1 behavior)
        if not request.url.path.startswith("/api/v2"):
            return await call_next(request)
        # Create cid as early as possible
        cid = getattr(request.state, "correlation_id", None)
        if cid is None:
            cid = get_or_create_correlation_id(request)
            request.state.correlation_id = cid
        try:
            response = await call_next(request)
        except Exception:
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error"},
            )
        response.headers[CORRELATION_ID_HEADER] = cid
        return response

app.add_middleware(V2CorrelationMiddleware)

# לצרף ראוטרים
app.include_router(strategy_router)
app.include_router(fx_router)
app.include_router(portfolio_router)
app.include_router(arbitrage_orch.router)
app.include_router(v2_router, prefix="/api/v2")
app.add_middleware(ErrorHandlingMiddleware)


@app.exception_handler(HTTPException)
async def http_exception_handler_with_v2_correlation(request: Request, exc: HTTPException) -> JSONResponse:
    # Apply only to V2
    if request.url.path.startswith("/api/v2"):
        cid = getattr(request.state, "correlation_id", None)
        if cid is None:
            cid = get_or_create_correlation_id(request)
        content = exc.detail
        if not isinstance(content, dict) or ("detail" not in content and "errors" not in content):
            content = {"detail": exc.detail}
        return JSONResponse(
            status_code=exc.status_code,
            content=content,
            headers={CORRELATION_ID_HEADER: cid},
        )
    # Non-V2: default behavior (do not attach correlation header)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
