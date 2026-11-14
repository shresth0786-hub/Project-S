from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.db.session import init_db
from app.api.videos import router as videos_router
from app.api.jobs import router as jobs_router
from app.api.auth import router as auth_router
from app.api.videos_list import router as list_router

setup_logging()

app = FastAPI(
    title="VisionX API",
    description="Multimodal AI Video Intelligence & Agentic RAG Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    try:
        init_db()
        logger.info("database_initialized")
    except Exception as e:
        logger.error("db_init_failed", error=str(e))

@app.get("/health")
def health():
    return {"status": "ok", "service": "visionx-backend", "version": "1.0.0"}

@app.get("/")
def root():
    return {"message": "VisionX API - See /docs for API documentation"}

# Routers
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(videos_router, prefix="/api/videos", tags=["videos"])
app.include_router(list_router, prefix="/api/videos", tags=["videos"])
app.include_router(jobs_router, prefix="/api/jobs", tags=["jobs"])

# Also mount timeline/chat etc via videos_router includes those paths

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("unhandled_exception", error=str(exc), path=str(request.url))
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "error": str(exc)})
