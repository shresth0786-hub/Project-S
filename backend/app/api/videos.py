import uuid
import os
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.config import settings
from app.schemas.video import VideoUploadResponse, VideoResponse, JobResponse, TimelineResponse, ChatRequest, ChatResponse, ReportRequest, ReportResponse
from app.models.video import Video
from app.models.processing_job import ProcessingJob
from app.models.transcript import TranscriptSegment
from app.models.frame import FrameObservation
from app.models.event import Event
from app.core.logging import logger
from app.services.storage import save_upload_file, get_video_path, delete_video_files
from app.services.video_processing import get_video_metadata
from app.core.security import get_current_user_optional

router = APIRouter()

ALLOWED = set(settings.allowed_types_list)
MAX_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

def trigger_processing(video_id: str):
    # Try celery, fallback to direct function call for dev without redis
    try:
        from worker.tasks.process_video import process_video_task
        process_video_task.delay(str(video_id))
        logger.info("celery_task_triggered", video_id=video_id)
    except Exception as e:
        logger.warning("celery_not_available_fallback", error=str(e))
        # Fallback synchronous for testing (run in background thread)
        try:
            from worker.tasks.process_video import process_video_sync
            import threading
            threading.Thread(target=process_video_sync, args=(str(video_id),), daemon=True).start()
        except Exception as e2:
            logger.error("fallback_failed", error=str(e2))

@router.post("", response_model=VideoUploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user = Depends(get_current_user_optional)
):
    if file.content_type not in ALLOWED:
        raise HTTPException(status_code=400, detail=f"Unsupported type {file.content_type}. Allowed: {ALLOWED}")
    # size check via reading? We'll check after save and delete if too large
    video_id = str(uuid.uuid4())
    # Validate extension
    dest, size = save_upload_file(file, video_id)
    if size > MAX_SIZE:
        try: Path(dest).unlink()
        except: pass
        raise HTTPException(status_code=400, detail=f"File too large {size} > {MAX_SIZE}")
    if size == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    meta = get_video_metadata(dest)
    video = Video(
        id=video_id,
        owner_id=getattr(user, 'id', None),
        filename=Path(dest).name,
        original_filename=file.filename or "video",
        file_path=dest,
        file_size=size,
        mime_type=file.content_type or "video/mp4",
        duration_seconds=meta.get("duration"),
        width=meta.get("width"),
        height=meta.get("height"),
        fps=meta.get("fps"),
        status="uploaded"
    )
    db.add(video)
    job = ProcessingJob(video_id=video_id, status="pending", current_step="queued", progress=0)
    db.add(job)
    db.commit()
    db.refresh(video)
    db.refresh(job)

    trigger_processing(video_id)

    return VideoUploadResponse(video_id=video.id, job_id=job.id, filename=video.filename, status=video.status, message="Upload successful, processing queued")

@router.get("/{video_id}", response_model=VideoResponse)
def get_video(video_id: uuid.UUID, db: Session = Depends(get_db)):
    v = db.query(Video).filter(Video.id == video_id).first()
    if not v:
        raise HTTPException(404, "Video not found")
    return v

@router.get("/{video_id}/stream")
def stream_video(video_id: uuid.UUID, db: Session = Depends(get_db)):
    v = db.query(Video).filter(Video.id == video_id).first()
    if not v:
        raise HTTPException(404, "Video not found")
    path = v.file_path
    if not Path(path).exists():
        # try fallback
        path = str(get_video_path(str(video_id)))
        if not Path(path).exists():
            raise HTTPException(404, "File not found on disk")
    return FileResponse(path, media_type=v.mime_type, filename=v.original_filename)

@router.delete("/{video_id}")
def delete_video(video_id: uuid.UUID, db: Session = Depends(get_db)):
    v = db.query(Video).filter(Video.id == video_id).first()
    if not v:
        raise HTTPException(404, "Video not found")
    delete_video_files(str(video_id))
    db.delete(v)
    db.commit()
    return {"deleted": True, "video_id": str(video_id)}

@router.get("/{video_id}/timeline", response_model=TimelineResponse)
def get_timeline(video_id: uuid.UUID, db: Session = Depends(get_db)):
    v = db.query(Video).filter(Video.id == video_id).first()
    if not v:
        raise HTTPException(404, "Video not found")
    events = db.query(Event).filter(Event.video_id == video_id).order_by(Event.start_time).all()
    segs = db.query(TranscriptSegment).filter(TranscriptSegment.video_id == video_id).order_by(TranscriptSegment.start_time).all()
    frames = db.query(FrameObservation).filter(FrameObservation.video_id == video_id).order_by(FrameObservation.timestamp).all()
    return TimelineResponse(
        video_id=v.id,
        duration=v.duration_seconds,
        events=[{"id": e.id, "event_type": e.event_type, "start_time": e.start_time, "end_time": e.end_time, "description": e.description, "confidence": e.confidence} for e in events],
        transcript_segments=[{"id": s.id, "start_time": s.start_time, "end_time": s.end_time, "text": s.text, "speaker": s.speaker} for s in segs],
        frames=[{"id": f.id, "timestamp": f.timestamp, "description": f.description, "frame_path": f.frame_path} for f in frames],
    )

@router.post("/{video_id}/chat", response_model=ChatResponse)
def chat_with_video(video_id: uuid.UUID, req: ChatRequest, db: Session = Depends(get_db)):
    v = db.query(Video).filter(Video.id == video_id).first()
    if not v:
        raise HTTPException(404, "Video not found")
    if v.status != "processed":
        # Allow but warn
        pass
    from app.services.rag import hybrid_search, build_context
    from app.services.llm import get_llm_provider
    from app.models.chat import ChatSession, ChatMessage
    import json

    # Retrieve evidence
    results = hybrid_search(db, str(video_id), req.message, top_k=req.top_k)
    context = build_context(results) if results else "No evidence found."

    # Session handling
    session_id = req.session_id
    if session_id:
        sess = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.video_id == video_id).first()
        if not sess:
            sess = ChatSession(id=session_id, video_id=video_id, title=req.message[:80])
            db.add(sess)
            db.commit()
            db.refresh(sess)
    else:
        sess = ChatSession(video_id=video_id, title=req.message[:80])
        db.add(sess)
        db.commit()
        db.refresh(sess)
        session_id = sess.id

    # Save user message
    db.add(ChatMessage(session_id=session_id, role="user", content=req.message))
    db.commit()

    # Generate answer via agent if available, else direct LLM
    try:
        from agent.graph import run_agent
        agent_out = run_agent(str(video_id), req.message, results, db)
        answer = agent_out.get("answer", "")
        citations = agent_out.get("citations", results)
        has_evidence = agent_out.get("has_sufficient_evidence", len(results) > 0)
    except Exception as e:
        # Fallback LLM
        provider = get_llm_provider()
        system = "You are VisionX, a video intelligence assistant. Answer ONLY using the provided evidence. Cite timestamps. If insufficient evidence, say so explicitly. Never fabricate timestamps."
        prompt = f"EVIDENCE:\n{context}\n\nQUESTION: {req.message}\n\nInstructions: Provide timestamp citations like [12.3s]. If no evidence, state insufficient evidence."
        answer = provider.generate(prompt, system=system)
        citations = results
        has_evidence = len(results) > 0 and "insufficient" not in answer.lower()

    # Save assistant message
    db.add(ChatMessage(session_id=session_id, role="assistant", content=answer, evidence_json=json.dumps([str(c.get('chunk_id')) for c in citations])))
    db.commit()

    # Build citation objects
    from app.schemas.video import Citation
    cites = []
    for r in citations[:req.top_k]:
        cites.append(Citation(chunk_id=r["chunk_id"], chunk_type=r["chunk_type"], content=r["content"][:500], timestamp=r.get("timestamp"), start_time=r.get("start_time"), end_time=r.get("end_time"), score=r.get("score"), video_id=r["video_id"]))

    return ChatResponse(answer=answer, citations=cites, session_id=session_id, has_sufficient_evidence=has_evidence, confidence="high" if has_evidence else "low")

@router.post("/{video_id}/reports", response_model=ReportResponse)
def create_report(video_id: uuid.UUID, req: ReportRequest, db: Session = Depends(get_db)):
    from app.models.report import GeneratedReport
    from app.services.llm import get_llm_provider
    from app.services.rag import hybrid_search, build_context
    v = db.query(Video).filter(Video.id == video_id).first()
    if not v:
        raise HTTPException(404, "Video not found")
    # Generate report based on all evidence
    chunks = hybrid_search(db, str(video_id), "summary of video content", top_k=20)
    context = build_context(chunks) if chunks else "No evidence."
    provider = get_llm_provider()
    prompt = f"Generate a {req.report_type} report for video {video_id}. EVIDENCE:\n{context}\nProvide title, summary, key events with timestamps."
    content = provider.generate(prompt, system="You are a report generator. Be concise, structured, timestamp-grounded.")
    title = req.title or f"{req.report_type.title()} Report - {v.original_filename}"
    report = GeneratedReport(video_id=video_id, report_type=req.report_type, title=title, content=content, structured_json=None)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

@router.get("/{video_id}/reports")
def list_reports(video_id: uuid.UUID, db: Session = Depends(get_db)):
    from app.models.report import GeneratedReport
    reports = db.query(GeneratedReport).filter(GeneratedReport.video_id == video_id).order_by(GeneratedReport.created_at.desc()).all()
    return reports

@router.get("/{video_id}/clip")
def extract_clip(video_id: uuid.UUID, start: float = Query(..., ge=0), end: float = Query(..., ge=0), db: Session = Depends(get_db)):
    import subprocess, tempfile
    v = db.query(Video).filter(Video.id == video_id).first()
    if not v:
        raise HTTPException(404, "Video not found")
    if end <= start:
        raise HTTPException(400, "end must be > start")
    if end - start > 60:
        raise HTTPException(400, "Clip max 60s")
    src = v.file_path
    out = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    out.close()
    cmd = ["ffmpeg", "-y", "-ss", str(start), "-to", str(end), "-i", src, "-c", "copy", out.name]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        # try re-encode
        cmd = ["ffmpeg", "-y", "-ss", str(start), "-to", str(end), "-i", src, "-c:v", "libx264", "-c:a", "aac", out.name]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            raise HTTPException(500, f"Clip extraction failed: {result.stderr.decode()[:500]}")
    return FileResponse(out.name, media_type="video/mp4", filename=f"clip_{start}_{end}.mp4")
