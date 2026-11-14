import json
import traceback
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.video import Video
from app.models.processing_job import ProcessingJob
from app.models.transcript import TranscriptSegment
from app.models.frame import FrameObservation
from app.models.detection import DetectedObject
from app.models.event import Event
from app.models.evidence import EvidenceChunk
from app.services.video_processing import extract_audio, extract_frames, detect_objects_yolo, transcribe_whisper, describe_frames_vision
from app.services.storage import get_audio_path, get_frames_dir
from app.services.embeddings import embed_batch
from app.core.logging import logger

try:
    from worker.celery_app import celery_app
    has_celery = True
except ImportError:
    has_celery = False
    celery_app = None

def update_job(db: Session, job: ProcessingJob, status=None, step=None, progress=None, error=None):
    if status: job.status = status
    if step: job.current_step = step
    if progress is not None: job.progress = progress
    if error: job.error = error
    db.commit()
    db.refresh(job)

def process_video_sync(video_id: str):
    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            logger.error("video_not_found", video_id=video_id)
            return
        job = db.query(ProcessingJob).filter(ProcessingJob.video_id == video_id).order_by(ProcessingJob.created_at.desc()).first()
        if not job:
            job = ProcessingJob(video_id=video_id, status="running", current_step="init", progress=0)
            db.add(job)
            db.commit()
            db.refresh(job)

        logger.info("processing_started", video_id=video_id)
        update_job(db, job, status="running", step="extracting_audio", progress=10)
        video.status = "processing"
        db.commit()

        # Step 1: audio
        audio_path = str(get_audio_path(video_id))
        ok_audio = extract_audio(video.file_path, audio_path)
        if not ok_audio:
            logger.warning("audio_extraction_failed_or_skipped", video_id=video_id)

        # Step 2: transcript
        update_job(db, job, step="transcribing", progress=30)
        segments = transcribe_whisper(audio_path) if Path(audio_path).exists() else []
        # Clear old
        db.query(TranscriptSegment).filter(TranscriptSegment.video_id == video_id).delete()
        for seg in segments:
            db.add(TranscriptSegment(video_id=video_id, start_time=seg["start"], end_time=seg["end"], text=seg["text"], language=seg.get("language","en")))
        db.commit()

        # Step 3: frames
        update_job(db, job, step="extracting_frames", progress=50)
        frames_dir = str(get_frames_dir(video_id))
        from app.core.config import settings
        frames = extract_frames(video.file_path, frames_dir, sample_fps=settings.FRAME_SAMPLE_FPS, scene_threshold=settings.SCENE_THRESHOLD)
        
        # Step 4: vision descriptions
        update_job(db, job, step="analyzing_frames", progress=65)
        db.query(FrameObservation).filter(FrameObservation.video_id == video_id).delete()
        descriptions = describe_frames_vision(frames)
        for f, desc in zip(frames, descriptions):
            db.add(FrameObservation(video_id=video_id, timestamp=desc["timestamp"], frame_path=desc["frame_path"], description=desc["description"], vision_model="mock"))
        db.commit()

        # Step 5: object detection
        update_job(db, job, step="detecting_objects", progress=75)
        db.query(DetectedObject).filter(DetectedObject.video_id == video_id).delete()
        detections = detect_objects_yolo(frames, video_id)
        # map timestamp to frame_id
        frame_map = {round(float(f.timestamp),2): f.id for f in db.query(FrameObservation).filter(FrameObservation.video_id==video_id).all()}
        for det in detections:
            fid = frame_map.get(round(det["timestamp"],2))
            db.add(DetectedObject(video_id=video_id, frame_id=fid, timestamp=det["timestamp"], label=det["label"], confidence=det["confidence"], bbox_x=det["bbox"][0], bbox_y=det["bbox"][1], bbox_w=det["bbox"][2], bbox_h=det["bbox"][3]))
        db.commit()

        # Step 6: events (simple heuristic: scene changes + mock sports)
        update_job(db, job, step="detecting_events", progress=85)
        db.query(Event).filter(Event.video_id == video_id).delete()
        for f in frames:
            if f.get("is_scene"):
                db.add(Event(video_id=video_id, event_type="scene_change", start_time=f["timestamp"], end_time=f["timestamp"]+0.5, description=f"Scene change at {f['timestamp']:.1f}s", confidence=0.7))
        # Mock sports events if detections contain ball/person patterns
        if any(d["label"]=="person" for d in detections):
            mid = (frames[len(frames)//2]["timestamp"] if frames else 5.0)
            db.add(Event(video_id=video_id, event_type="player_movement", start_time=mid, end_time=mid+2, description="Player movement detected", confidence=0.65))
        db.commit()

        # Step 7: embeddings & evidence chunks
        update_job(db, job, step="indexing", progress=90)
        db.query(EvidenceChunk).filter(EvidenceChunk.video_id == video_id).delete()
        # Build chunks: transcripts + frames + events
        chunks_to_embed = []
        meta_list = []
        segs = db.query(TranscriptSegment).filter(TranscriptSegment.video_id==video_id).all()
        for s in segs:
            txt = f"[Transcript {s.start_time:.1f}-{s.end_time:.1f}s]: {s.text}"
            chunks_to_embed.append(txt)
            meta_list.append({"type":"transcript","id":str(s.id),"start":s.start_time,"end":s.end_time,"ts":s.start_time})
        frs = db.query(FrameObservation).filter(FrameObservation.video_id==video_id).all()
        for fr in frs:
            txt = f"[Frame {fr.timestamp:.1f}s]: {fr.description}"
            chunks_to_embed.append(txt)
            meta_list.append({"type":"frame","id":str(fr.id),"ts":fr.timestamp})
        evs = db.query(Event).filter(Event.video_id==video_id).all()
        for ev in evs:
            txt = f"[Event {ev.event_type} {ev.start_time:.1f}s]: {ev.description}"
            chunks_to_embed.append(txt)
            meta_list.append({"type":"event","id":str(ev.id),"start":ev.start_time,"end":ev.end_time,"ts":ev.start_time})

        if chunks_to_embed:
            embeddings = embed_batch(chunks_to_embed)
            for txt, meta, emb in zip(chunks_to_embed, meta_list, embeddings):
                # For pgvector, pass list; for sqlite test, store json
                try:
                    chunk = EvidenceChunk(
                        video_id=video_id,
                        chunk_type=meta["type"],
                        source_id=meta["id"],
                        content=txt,
                        start_time=meta.get("start"),
                        end_time=meta.get("end"),
                        timestamp=meta.get("ts"),
                        meta_json=json.dumps(meta),
                        embedding=emb
                    )
                except Exception:
                    chunk = EvidenceChunk(
                        video_id=video_id,
                        chunk_type=meta["type"],
                        source_id=meta["id"],
                        content=txt,
                        start_time=meta.get("start"),
                        end_time=meta.get("end"),
                        timestamp=meta.get("ts"),
                        meta_json=json.dumps(meta),
                        embedding=json.dumps(emb)
                    )
                db.add(chunk)
            db.commit()

        update_job(db, job, status="completed", step="completed", progress=100)
        job.finished_at = datetime.utcnow()
        video.status = "processed"
        db.commit()
        logger.info("processing_completed", video_id=video_id, chunks=len(chunks_to_embed))

    except Exception as e:
        tb = traceback.format_exc()
        logger.error("processing_failed", video_id=video_id, error=str(e), traceback=tb)
        try:
            job = db.query(ProcessingJob).filter(ProcessingJob.video_id == video_id).order_by(ProcessingJob.created_at.desc()).first()
            if job:
                update_job(db, job, status="failed", step="failed", error=str(e)[:2000])
            video = db.query(Video).filter(Video.id == video_id).first()
            if video:
                video.status = "failed"
                video.error_message = str(e)[:1000]
                db.commit()
        except Exception as e2:
            logger.error("error_updating_failure", error=str(e2))
    finally:
        db.close()

if has_celery:
    @celery_app.task(name="process_video", bind=True, max_retries=2)
    def process_video_task(self, video_id: str):
        try:
            process_video_sync(video_id)
        except Exception as exc:
            # Retry
            raise self.retry(exc=exc, countdown=5)
