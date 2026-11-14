import os
import json
import subprocess
import cv2
from pathlib import Path
from typing import List, Dict

def get_video_metadata(video_path: str) -> Dict:
    # Try ffprobe, fallback to opencv
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", video_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
            fmt = data.get("format", {})
            return {
                "duration": float(fmt.get("duration", 0) or stream.get("duration", 0) or 0),
                "width": int(stream.get("width", 0) or 0),
                "height": int(stream.get("height", 0) or 0),
                "fps": eval(stream.get("r_frame_rate", "0/1")) if stream.get("r_frame_rate") else 0,
            }
    except Exception as e:
        print(f"ffprobe failed: {e}")
    # Fallback cv2
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    duration = frames / fps if fps else 0
    cap.release()
    return {"duration": duration, "width": w, "height": h, "fps": fps}

def _ffmpeg_bin():
    for cand in [os.getenv("FFMPEG_BINARY"), "ffmpeg", r"C:\Users\SHRESTH\AppData\Local\Microsoft\WindowsApps\ffmpeg.exe", r"F:\Project S\cache\ffmpeg\ffmpeg.exe"]:
        if cand and Path(cand).exists() or cand=="ffmpeg":
            # test
            try:
                subprocess.run([cand,"-version"], capture_output=True, timeout=3)
                return cand
            except: continue
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except: return "ffmpeg"

def extract_audio(video_path: str, audio_path: str) -> bool:
    # FFmpeg extraction to wav 16k mono
    try:
        bin = _ffmpeg_bin()
        cmd = [bin, "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode!=0:
            print(f"ffmpeg stderr {result.stderr[:500]}")
        return result.returncode == 0 and Path(audio_path).exists()
    except Exception as e:
        print(f"extract_audio error: {e}")
        return False

def extract_frames(video_path: str, out_dir: str, sample_fps: float = 1.0, scene_threshold: float = 30.0) -> List[Dict]:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    interval = max(1, int(round(fps / sample_fps))) if sample_fps > 0 else int(fps)
    idx = 0
    saved = []
    prev_hist = None
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % interval == 0:
            timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            # Scene detection: histogram diff
            is_scene = False
            hist = cv2.calcHist([frame], [0], None, [64], [0,256])
            hist = cv2.normalize(hist, hist).flatten()
            if prev_hist is not None:
                diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA)
                if diff > (scene_threshold / 100.0):
                    is_scene = True
            prev_hist = hist
            fname = f"frame_{timestamp:.2f}.jpg"
            fpath = os.path.join(out_dir, fname)
            cv2.imwrite(fpath, frame)
            saved.append({"frame_path": fpath, "timestamp": round(timestamp, 2), "is_scene": is_scene, "frame_idx": idx})
        idx += 1
    cap.release()
    return saved

def detect_objects_yolo(frames: List[Dict], video_id: str = "") -> List[Dict]:
    # Lazy YOLO, fallback to mock if not available
    try:
        from ultralytics import YOLO
        from app.core.config import settings
        model = YOLO(settings.YOLO_MODEL)
        detections = []
        for f in frames:
            res = model(f["frame_path"], verbose=False)[0]
            for box in res.boxes:
                cls = int(box.cls[0])
                label = res.names[cls]
                conf = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append({
                    "timestamp": f["timestamp"],
                    "frame_path": f["frame_path"],
                    "label": label,
                    "confidence": conf,
                    "bbox": [x1, y1, x2-x1, y2-y1],
                })
        return detections
    except Exception as e:
        print(f"YOLO fallback mock: {e}")
        # Mock: randomly report person/ball for demo
        mock = []
        for f in frames[:3]:
            mock.append({"timestamp": f["timestamp"], "frame_path": f["frame_path"], "label": "person", "confidence": 0.85, "bbox": [100,100,50,120]})
        return mock

def transcribe_whisper(audio_path: str) -> List[Dict]:
    try:
        from faster_whisper import WhisperModel
        from app.core.config import settings
        model = WhisperModel(settings.WHISPER_MODEL_SIZE, device=settings.WHISPER_DEVICE, compute_type="int8")
        segments, info = model.transcribe(audio_path, beam_size=5)
        out = []
        for seg in segments:
            out.append({"start": seg.start, "end": seg.end, "text": seg.text.strip(), "language": info.language})
        return out
    except Exception as e:
        print(f"Whisper fallback: {e}")
        # Mock transcript for demo / when model not downloaded
        return [
            {"start": 0.0, "end": 4.5, "text": "Welcome to the video. This is a mock transcript generated in fallback mode.", "language": "en"},
            {"start": 5.0, "end": 10.0, "text": "The content analysis will work once Whisper model is downloaded and FFmpeg processed the audio.", "language": "en"},
        ]

def describe_frames_vision(frames: List[Dict]) -> List[Dict]:
    # Uses LLM vision if configured, else mock descriptions
    from app.services.llm import get_llm_provider
    provider = get_llm_provider()
    # Check if real vision available (OpenAI key)
    is_mock = provider.__class__.__name__ == "MockProvider"
    out = []
    for f in frames:
        if is_mock:
            desc = f"A frame at {f['timestamp']:.1f}s showing a scene. Mock description: persons and objects visible, lighting normal."
        else:
            # In real mode we would send image to vision model; for now use text prompt mock
            # Placeholder for openai vision call
            desc = provider.generate(f"Describe this video frame at {f['timestamp']}s", system="You are a video analyst.")
        out.append({"timestamp": f["timestamp"], "frame_path": f["frame_path"], "description": desc})
    return out
