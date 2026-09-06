import sys
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import AppException
from app.database.connection import init_db, check_db_health
from app.api.v1.router import api_v1_router
from app.schemas.errors import ErrorResponse, ErrorDetail

# Initialize structured logging
setup_logging(debug=settings.DEBUG)
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan event handler for startup and shutdown procedures."""
    logger.info("Starting SIH26104 Voice Cloning Detection Backend...")
    # Initialize DB schemas on startup if needed (e.g. SQLite / dev fallback)
    try:
        await init_db()
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to auto-initialize DB: {e}")
    yield
    logger.info("Shutting down backend...")


app = FastAPI(
    title="SIH26104 Voice Cloning Detection & Prevention Backend",
    description="Real-Time Detection and Prevention of Voice Cloning Impersonation Attacks API.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware for Frontend (Member 4)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers ensuring consistent ErrorResponse shape
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    error_payload = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code=exc.code,
            message=exc.message,
            details=exc.details,
        ),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload.model_dump(mode="json"),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    first_error = exc.errors()[0] if exc.errors() else {"loc": ["body"], "msg": "Validation error"}
    field_name = ".".join(str(loc) for loc in first_error.get("loc", []))
    error_payload = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message=first_error.get("msg", "Validation error"),
            field=field_name,
            details={"errors": exc.errors()},
        ),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_payload.model_dump(mode="json"),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled server exception: {exc}")
    error_payload = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred.",
            details={"type": type(exc).__name__} if settings.DEBUG else None,
        ),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_payload.model_dump(mode="json"),
    )


# Health check route
@app.get(
    "/health",
    tags=["System"],
    summary="System and Database Health Check",
    status_code=status.HTTP_200_OK,
)
async def health_check():
    """Verifies that the backend server is running and the database connection is healthy."""
    db_healthy = await check_db_health()
    if not db_healthy:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "database": "disconnected"},
        )
    return {"status": "healthy", "database": "connected", "version": "1.0.0"}


# Serve Interactive Dashboard UI/UX
@app.get("/", tags=["Dashboard"], include_in_schema=False)
@app.get("/dashboard", tags=["Dashboard"], include_in_schema=False)
async def serve_dashboard():
    """Serves the interactive real-time VoiceShield AI console."""
    from fastapi.responses import FileResponse
    dashboard_path = os.path.join(os.path.dirname(__file__), "app", "static", "dashboard.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    return {"message": "VoiceShield AI Backend is Running. Visit /docs for API documentation."}


# Mount API routers
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
