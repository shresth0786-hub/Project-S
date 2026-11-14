import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
try:
    from pgvector.sqlalchemy import Vector
    has_vector = True
except ImportError:
    has_vector = False
    Vector = None

class EvidenceChunk(Base):
    __tablename__ = "evidence_chunks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_type = Column(String(50), nullable=False)  # transcript, frame, object, event
    source_id = Column(String(100), nullable=True)  # reference to original table id
    content = Column(Text, nullable=False)
    start_time = Column(Float, nullable=True)
    end_time = Column(Float, nullable=True)
    timestamp = Column(Float, nullable=True)
    meta_json = Column(Text, nullable=True)
    # Use Vector if available else Text placeholder for testing
    if has_vector:
        embedding = Column(Vector(384), nullable=True)
    else:
        embedding = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    video = relationship("Video", back_populates="evidence_chunks")
