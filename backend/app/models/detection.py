import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.session import Base

class DetectedObject(Base):
    __tablename__ = "detected_objects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    frame_id = Column(UUID(as_uuid=True), ForeignKey("frame_observations.id", ondelete="CASCADE"), nullable=True)
    timestamp = Column(Float, nullable=False)
    label = Column(String(100), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    bbox_x = Column(Float, nullable=True)
    bbox_y = Column(Float, nullable=True)
    bbox_w = Column(Float, nullable=True)
    bbox_h = Column(Float, nullable=True)
    track_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
