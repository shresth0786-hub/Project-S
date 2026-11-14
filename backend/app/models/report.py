import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.session import Base

class GeneratedReport(Base):
    __tablename__ = "generated_reports"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    report_type = Column(String(50), nullable=False)  # summary, analytics, sports
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    structured_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
