# VisionX Architecture

## System Diagram
```
[Next.js Frontend] --REST--> [FastAPI Backend] --Celery--> [Worker Pipelines]
     |                           |                             |
  VideoPlayer              PostgreSQL+pgvector            FFmpeg/OpenCV
  Upload                   Redis                         Whisper/YOLO
  Timeline                 EvidenceChunks                 Embeddings
  Chat                     LangGraph Agents
```

## DB Schema
- users, videos, processing_jobs, transcript_segments, frame_observations, detected_objects, events, evidence_chunks (vector), chat_sessions, chat_messages, generated_reports
- All indexed records have video_id + timestamp

## RAG Flow
Query → embed → hybrid search (vector+BM25) → rerank → compress → LLM grounded with citations

## Agent Flow
See agent/graph.py — supervisor classifies intent, routes, validates, generates.

## Optimizations
- Async Celery, parallel audio+frame, embedding batching, Redis cache, adaptive FPS, streaming responses
