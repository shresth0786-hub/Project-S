import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class FrameObservation(Base):
    __tablename__ = "frame_observations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(Float, nullable=False, index=True)
    frame_path = Column(String(1000), nullable=True)
    description = Column(Text, nullable=True)
    vision_model = Column(String(100), nullable=True)
    objects_json = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    video = relationship("Video", back_populates="frames")
