import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.video import JobResponse
from app.models.processing_job import ProcessingJob

router = APIRouter()

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    j = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not j:
        raise HTTPException(404, "Job not found")
    return j
