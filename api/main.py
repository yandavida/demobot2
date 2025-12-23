from __future__ import annotations

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

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

# לצרף ראוטרים
app.include_router(strategy_router)
app.include_router(fx_router)
app.include_router(portfolio_router)
app.include_router(arbitrage_orch.router)

app.include_router(v2_router)
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
