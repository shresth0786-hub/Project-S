from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class VideoUploadResponse(BaseModel):
    video_id: UUID
    job_id: UUID
    filename: str
    status: str
    message: str

class VideoResponse(BaseModel):
    id: UUID
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    duration_seconds: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class JobResponse(BaseModel):
    id: UUID
    video_id: UUID
    status: str
    current_step: str
    progress: int
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TimelineEvent(BaseModel):
    id: UUID
    event_type: str
    start_time: float
    end_time: float
    description: Optional[str] = None
    confidence: Optional[float] = None

class TimelineSegment(BaseModel):
    id: UUID
    start_time: float
    end_time: float
    text: str
    speaker: Optional[str] = None

class TimelineFrame(BaseModel):
    id: UUID
    timestamp: float
    description: Optional[str] = None
    frame_path: Optional[str] = None

class TimelineResponse(BaseModel):
    video_id: UUID
    duration: Optional[float] = None
    events: List[TimelineEvent]
    transcript_segments: List[TimelineSegment]
    frames: List[TimelineFrame]

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[UUID] = None
    top_k: int = Field(default=5, ge=1, le=20)
    include_timestamps: bool = True

class Citation(BaseModel):
    chunk_id: UUID
    chunk_type: str
    content: str
    timestamp: Optional[float] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    score: Optional[float] = None
    video_id: UUID

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    session_id: UUID
    confidence: Optional[str] = None
    has_sufficient_evidence: bool = True

class ReportRequest(BaseModel):
    report_type: str = Field(default="summary", pattern="^(summary|analytics|sports|detailed)$")
    title: Optional[str] = None

class ReportResponse(BaseModel):
    id: UUID
    video_id: UUID
    report_type: str
    title: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=6)
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID
