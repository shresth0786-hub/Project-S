import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.session import Base

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    current_step = Column(String(100), default="queued")
    progress = Column(Integer, default=0)  # 0-100
    error = Column(Text, nullable=True)
    retries = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
