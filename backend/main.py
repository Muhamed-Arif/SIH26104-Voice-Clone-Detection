import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import get_logger, setup_logging
from app.database.connection import check_db_health, init_db
from app.schemas.errors import ErrorDetail, ErrorResponse

setup_logging(debug=settings.DEBUG)
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting SIH26104 Voice Cloning Detection Backend...")
    try:
        await init_db()
        logger.info("Database schema initialized successfully.")
    except Exception as exc:
        logger.error("Failed to auto-initialize DB: %s", exc)
    yield
    logger.info("Shutting down backend...")


app = FastAPI(
    title="SIH26104 Voice Cloning Detection & Prevention Backend",
    description="Real-Time Detection and Prevention of Voice Cloning Impersonation Attacks API.",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    payload = ErrorResponse(success=False, error=ErrorDetail(code=exc.code, message=exc.message, details=exc.details))
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    first_error = exc.errors()[0] if exc.errors() else {"loc": ["body"], "msg": "Validation error"}
    field_name = ".".join(str(loc) for loc in first_error.get("loc", []))
    payload = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message=first_error.get("msg", "Validation error"),
            field=field_name,
            details={"errors": exc.errors()},
        ),
    )
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload.model_dump(mode="json"))


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server exception: %s", exc)
    payload = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred.",
            details={"type": type(exc).__name__} if settings.DEBUG else None,
        ),
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload.model_dump(mode="json"))


@app.get("/health", tags=["System"], summary="Backend and database health")
async def health_check():
    db_healthy = await check_db_health()
    if not db_healthy:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "database": "disconnected", "version": "1.1.0"},
        )
    return {"status": "healthy", "database": "connected", "version": "1.1.0"}


@app.get("/integration-health", tags=["System"], summary="Backend, database and M1 health")
async def integration_health():
    db_healthy = await check_db_health()
    ml_health_url = settings.ML_SERVICE_URL.rsplit("/predict", 1)[0] + "/health"
    ml_payload = {"status": "unreachable"}
    ml_healthy = False
    try:
        async with httpx.AsyncClient(timeout=settings.ML_REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(ml_health_url)
            if response.status_code == 200:
                ml_payload = response.json()
                ml_healthy = ml_payload.get("status") == "ok"
            else:
                ml_payload = {"status": "error", "http_status": response.status_code}
    except Exception as exc:
        ml_payload = {"status": "unreachable", "error": str(exc)}

    overall = db_healthy and ml_healthy
    return JSONResponse(
        status_code=200 if overall else 503,
        content={
            "status": "ok" if overall else "degraded",
            "database": "connected" if db_healthy else "disconnected",
            "ml": ml_payload,
            "mock_ml": settings.MOCK_ML_SERVICE,
            "version": "1.1.0",
        },
    )


@app.get("/", tags=["Frontend"], include_in_schema=False)
async def serve_integrated_frontend():
    path = os.path.join(os.path.dirname(__file__), "app", "static", "integrated.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"message": "Integrated frontend missing. Visit /docs for API documentation."}


@app.get("/legacy-dashboard", tags=["Frontend"], include_in_schema=False)
async def serve_legacy_dashboard():
    path = os.path.join(os.path.dirname(__file__), "app", "static", "dashboard.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"message": "Legacy dashboard not available."}


app.include_router(api_v1_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
