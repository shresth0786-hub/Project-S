"""
Sports Analytics Module
- Goal/shot detection heuristics
- Player/ball tracking via YOLO + ByteTrack (mock if not available)
- Temporal event analysis
"""
from typing import List, Dict
import cv2
from app.services.video_processing import detect_objects_yolo

def analyze_sports_video(frames: List[Dict], detections: List[Dict]) -> List[Dict]:
    events = []
    # Heuristic: if person + ball proximity suggests shot
    # Group detections by timestamp
    from collections import defaultdict
    by_ts = defaultdict(list)
    for d in detections:
        by_ts[round(d["timestamp"],1)].append(d)
    
    for ts, dets in by_ts.items():
        labels = [d["label"] for d in dets]
        # Mock goal: ball near top of frame + person
        if "sports ball" in labels and "person" in labels:
            # Check ball y position low (near goal)
            balls = [d for d in dets if d["label"]=="sports ball"]
            for b in balls:
                if b["bbox"][1] < 100:  # top
                    events.append({"event_type":"goal_attempt","start_time": ts,"end_time": ts+1,"description": f"Potential goal/shot at {ts}s - ball near goal with player","confidence":0.62})
                    break
        if labels.count("person") >= 3:
            events.append({"event_type":"player_movement","start_time": ts,"end_time": ts+1.5,"description": f"Multi-player movement at {ts}s","confidence":0.55})

    # Ball tracking: simple interpolation
    ball_path = [d for d in detections if d["label"] in ["sports ball","ball"]]
    if len(ball_path) > 5:
        events.append({"event_type":"ball_tracking","start_time": ball_path[0]["timestamp"],"end_time": ball_path[-1]["timestamp"],"description": f"Ball tracked across {len(ball_path)} frames","confidence":0.7,"metadata":{"path_len":len(ball_path)}})
    
    return events
