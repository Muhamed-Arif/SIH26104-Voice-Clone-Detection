from fastapi import APIRouter
from app.api.v1.sessions import router as sessions_router
from app.api.v1.analyze import router as analyze_router
from app.api.v1.stream import router as stream_router
from app.api.v1.results import router as results_router
from app.api.v1.verify import router as verify_router

api_v1_router = APIRouter()

api_v1_router.include_router(sessions_router)
api_v1_router.include_router(analyze_router)
api_v1_router.include_router(stream_router)
api_v1_router.include_router(results_router)
api_v1_router.include_router(verify_router)
