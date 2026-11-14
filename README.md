# VisionX — Multimodal AI Video Intelligence & Agentic RAG Platform

> Upload video → Understand content → Chat with timestamped evidence → Generate reports → Sports analytics

## Architecture
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind, Zustand
- **Backend**: FastAPI, Pydantic, SQLAlchemy, PostgreSQL + pgvector
- **Media**: FFmpeg, OpenCV, faster-whisper, YOLOv8, Vision LLM
- **RAG**: sentence-transformers/all-MiniLM-L6-v2 (384d), hybrid vector+keyword, cross-encoder rerank (fallback), metadata filtering
- **Agents**: LangGraph Supervisor → Retrieval, Vision, Event Detection, Evidence Validation, Report Generation
- **Infra**: Docker Compose, Redis, Celery, LangSmith tracing

## Quick Start
```bash
cp .env.example .env
# Set OPENAI_API_KEY for full LLM, else mock mode runs locally
docker compose up --build
# Frontend http://localhost:3000
# Backend  http://localhost:8000/docs
```

Without Docker (dev):
```bash
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload
# In another terminal
celery -A worker.celery_app worker --loglevel=info
cd frontend && npm install && npm run dev
```

## API Endpoints
- `POST /api/videos` — upload video (multipart)
- `GET /api/videos/{id}` — get video metadata
- `GET /api/videos` — list videos
- `GET /api/jobs/{job_id}` — job status
- `GET /api/videos/{id}/timeline` — transcript + frames + events
- `POST /api/videos/{id}/chat` — agentic RAG chat with citations
- `POST /api/videos/{id}/reports` — generate summary/analytics/sports report
- `DELETE /api/videos/{id}` — secure delete
- `GET /api/videos/{id}/stream` — video streaming
- `GET /api/videos/{id}/clip?start=5&end=10` — extract clip
- `POST /api/auth/register` / `login`

See Swagger at `/docs`.

## Processing Pipeline
1. Validate & store video → create ProcessingJob
2. Celery task: FFmpeg audio extract → faster-whisper timestamped transcript
3. OpenCV frame sampling (1 fps, scene detection) → vision descriptions
4. YOLOv8 detection (optional ByteTrack)
5. Normalize → EvidenceChunks (transcript/frame/object/event) → embed → pgvector
6. Mark processed

Retries, failure handling, job tracking included. HTTP never blocks.

## RAG
- Index: transcript segments, frame descriptions, detections, events
- Hybrid: `score = 0.7*cosine + 0.3*keyword`
- Metadata filter by video, type, time range
- Context compression (600 chars/chunk, annotated [idx][timestamp])
- Source-grounded generation, explicit uncertainty if insufficient evidence
- Never fabricates timestamps

## Agents (LangGraph)
```
supervisor → retrieval → [vision|event] → validation → report → END
```
Typed state, conditional edges, tool schemas.

## Sports Module
YOLO + ByteTrack + temporal heuristics; events with confidence & timestamps; extensible to SoccerNet evaluation.

## Content Generation
Modular: `generate_summary`, text-to-image (OpenAI DALL·E interface, mock if no key), TTS placeholder.

## Evaluation
```bash
python evals/metrics.py
python evals/run_evals.py
pytest tests/
```
Metrics: P@K, R@K, MRR, faithfulness, citation correctness, P50/P95 latency, sports P/R/F1.

## Versions
See `backend/requirements.txt` and `frontend/package.json` — all pinned.

## Security
- JWT auth, file type/size validation, rate limit hook, env config, safe storage, secure deletion.

## .env
Copy `.env.example`, never hardcode keys.

## Deployment
`docker compose` ready; add S3 for storage, set `LANGCHAIN_TRACING_V2=true` for LangSmith.

## License
MIT for code; models/datasets respect original licenses (Whisper, YOLO, SoccerNet).
