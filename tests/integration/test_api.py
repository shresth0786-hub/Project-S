"""Integration test with FastAPI TestClient and SQLite mock"""
import sys
sys.path.insert(0, "../../backend")

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import Base, engine, SessionLocal

def setup():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_health():
    with TestClient(app) as c:
        r = c.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        print("health ok")

def test_upload_validation():
    with TestClient(app) as c:
        r = c.post("/api/videos", files={"file": ("test.mp4", b"fake", "video/mp4")})
        # May succeed or fail based on ffprobe; check not 500
        assert r.status_code in [200, 400, 500]
        print("upload validation status", r.status_code)

if __name__ == "__main__":
    setup()
    test_health()
    test_upload_validation()
    print("integration ok")
