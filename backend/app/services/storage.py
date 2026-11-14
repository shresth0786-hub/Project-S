import os
import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile
from app.core.config import settings

STORAGE_ROOT = Path(settings.STORAGE_ROOT)
VIDEOS_DIR = STORAGE_ROOT / "videos"
AUDIO_DIR = STORAGE_ROOT / "audio"
FRAMES_DIR = STORAGE_ROOT / "frames"

for d in [VIDEOS_DIR, AUDIO_DIR, FRAMES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def save_upload_file(upload_file: UploadFile, video_id: str) -> tuple[str, int]:
    ext = Path(upload_file.filename or "video.mp4").suffix or ".mp4"
    filename = f"{video_id}{ext}"
    dest = VIDEOS_DIR / filename
    size = 0
    with open(dest, "wb") as f:
        while True:
            chunk = upload_file.file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            f.write(chunk)
    return str(dest), size

def _norm_id(video_id) -> str:
    return str(video_id)

def get_video_path(video_id: str, ext: str = ".mp4") -> Path:
    vid = _norm_id(video_id)
    for p in VIDEOS_DIR.glob(f"{vid}.*"):
        return p
    return VIDEOS_DIR / f"{vid}{ext}"

def delete_video_files(video_id: str):
    vid = _norm_id(video_id)
    for p in VIDEOS_DIR.glob(f"{vid}.*"):
        try:
            p.unlink()
        except: pass
    for p in AUDIO_DIR.glob(f"{vid}.*"):
        try:
            p.unlink()
        except: pass
    frame_dir = FRAMES_DIR / vid
    if frame_dir.exists():
        shutil.rmtree(frame_dir, ignore_errors=True)

def get_audio_path(video_id: str) -> Path:
    return AUDIO_DIR / f"{_norm_id(video_id)}.wav"

def get_frames_dir(video_id: str) -> Path:
    d = FRAMES_DIR / _norm_id(video_id)
    d.mkdir(parents=True, exist_ok=True)
    return d
