from __future__ import annotations

from fastapi import FastAPI

from api.logging_config import configure_logging
from api.routers.fx_router import router as fx_router
from api.routers.strategy_router import router as strategy_router
from api.middleware.errors import ErrorHandlingMiddleware

# להגדיר לוגים לפני יצירת האפליקציה
configure_logging()

app = FastAPI(
    title="DemoBot SaaS API",
    version="0.1.0",
)

# לצרף ראוטרים
app.include_router(strategy_router)
app.include_router(fx_router)
app.add_middleware(ErrorHandlingMiddleware)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
