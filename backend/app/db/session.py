from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Sync engine for simplicity; async can be added later
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from app.models import user, video, processing_job, transcript, frame, detection, event, evidence, chat, report  # noqa
    Base.metadata.create_all(bind=engine)
    # Enable pgvector extension if postgres
    try:
        with engine.begin() as conn:
            conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector;")
    except Exception as e:
        print(f"pgvector extension not enabled (maybe SQLite test): {e}")
