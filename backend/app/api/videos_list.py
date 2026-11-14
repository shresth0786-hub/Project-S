from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.video import Video

router = APIRouter()

@router.get("")
def list_videos(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    q = db.query(Video).order_by(Video.created_at.desc()).offset(skip).limit(limit).all()
    return q
