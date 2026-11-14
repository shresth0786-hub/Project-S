from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.services.rag import hybrid_search

def video_search(db: Session, video_id: str, query: str, top_k: int = 5) -> List[Dict]:
    """Hybrid search across all evidence types"""
    return hybrid_search(db, video_id, query, top_k=top_k)

def transcript_search(db: Session, video_id: str, query: str, top_k: int = 5) -> List[Dict]:
    return hybrid_search(db, video_id, query, top_k=top_k, chunk_type_filter="transcript")

def frame_analyzer(db: Session, video_id: str, timestamp: float) -> Dict:
    from app.models.frame import FrameObservation
    # Find nearest frame
    frames = db.query(FrameObservation).filter(FrameObservation.video_id==video_id).order_by(FrameObservation.timestamp).all()
    if not frames:
        return {"error": "No frames found"}
    nearest = min(frames, key=lambda f: abs(f.timestamp - timestamp))
    return {"timestamp": nearest.timestamp, "description": nearest.description, "frame_path": nearest.frame_path, "distance": abs(nearest.timestamp - timestamp)}

def event_detector(db: Session, video_id: str, event_type: Optional[str] = None) -> List[Dict]:
    from app.models.event import Event
    q = db.query(Event).filter(Event.video_id==video_id)
    if event_type:
        q = q.filter(Event.event_type==event_type)
    events = q.order_by(Event.start_time).all()
    return [{"event_type": e.event_type, "start": e.start_time, "end": e.end_time, "description": e.description, "confidence": e.confidence} for e in events]

def timestamp_retriever(db: Session, video_id: str, query: str) -> List[Dict]:
    # Retrieve with strong timestamp grounding
    results = hybrid_search(db, video_id, query, top_k=5)
    return [{"timestamp": r.get("timestamp") or r.get("start_time"), "content": r["content"], "score": r["score"]} for r in results]

def extract_video_clip(video_path: str, start: float, end: float, out_path: str) -> str:
    import subprocess
    cmd = ["ffmpeg", "-y", "-ss", str(start), "-to", str(end), "-i", video_path, "-c", "copy", out_path]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0:
        cmd = ["ffmpeg", "-y", "-ss", str(start), "-to", str(end), "-i", video_path, "-c:v", "libx264", "-c:a", "aac", out_path]
        res = subprocess.run(cmd, capture_output=True)
    return out_path if res.returncode==0 else ""

def generate_summary(db: Session, video_id: str) -> str:
    from app.services.rag import hybrid_search, build_context
    from app.services.llm import get_llm_provider
    chunks = hybrid_search(db, video_id, "summary", top_k=10)
    ctx = build_context(chunks) if chunks else "No evidence"
    provider = get_llm_provider()
    return provider.generate(f"EVIDENCE:\n{ctx}\n\nQUESTION: Summarize video concisely with timestamps.", system="You are a summarizer.")

def generate_report(db: Session, video_id: str, report_type: str = "summary") -> str:
    return generate_summary(db, video_id)
