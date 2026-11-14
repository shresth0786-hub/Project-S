from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://visionx:visionx@localhost:5432/visionx"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    JWT_SECRET_KEY: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    STORAGE_ROOT: str = "./storage"
    MAX_UPLOAD_SIZE_MB: int = 500
    ALLOWED_VIDEO_TYPES: str = "video/mp4,video/quicktime,video/x-matroska,video/webm,video/avi"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    LANGSMITH_API_KEY: Optional[str] = None
    LANGCHAIN_TRACING_V2: bool = False
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    LLM_MODEL: str = "gpt-4o-mini"
    VISION_MODEL: str = "gpt-4o-mini"
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_DEVICE: str = "cpu"
    YOLO_MODEL: str = "yolov8n.pt"
    FRAME_SAMPLE_FPS: float = 1.0
    SCENE_THRESHOLD: float = 30.0
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def allowed_types_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_VIDEO_TYPES.split(",")]

settings = Settings()
