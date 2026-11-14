import uuid
from sqlalchemy import Column, String, DateTime, Float, Integer, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum

class VideoStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    processed = "processed"
    failed = "failed"

class Video(Base):
    __tablename__ = "videos"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    duration_seconds = Column(Float, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    fps = Column(Float, nullable=True)
    status = Column(String(20), default=VideoStatus.uploaded.value)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    segments = relationship("TranscriptSegment", back_populates="video", cascade="all, delete-orphan")
    frames = relationship("FrameObservation", back_populates="video", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="video", cascade="all, delete-orphan")
    evidence_chunks = relationship("EvidenceChunk", back_populates="video", cascade="all, delete-orphan")
