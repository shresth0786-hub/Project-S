import json
import re
import numpy as np
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text, or_
from app.models.evidence import EvidenceChunk
from app.services.embeddings import embed_text
from app.core.config import settings

# Hybrid search: vector + keyword (BM25-like via SQL ILIKE) + metadata filtering
# Reranking: simple cross-encoder fallback to cosine

def cosine_sim(a, b):
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)

def keyword_score(query: str, content: str) -> float:
    q_terms = re.findall(r"\w+", query.lower())
    c_lower = content.lower()
    if not q_terms:
        return 0
    hits = sum(1 for t in q_terms if t in c_lower)
    return hits / len(q_terms)

def hybrid_search(
    db: Session,
    video_id: str,
    query: str,
    top_k: int = 5,
    chunk_type_filter: Optional[str] = None,
    start_time_filter: Optional[float] = None,
    end_time_filter: Optional[float] = None,
    alpha: float = 0.7,  # weight for vector vs keyword
) -> List[Dict]:
    # Embed query
    q_emb = embed_text(query)
    
    # Base query
    q = db.query(EvidenceChunk).filter(EvidenceChunk.video_id == video_id)
    if chunk_type_filter:
        q = q.filter(EvidenceChunk.chunk_type == chunk_type_filter)
    if start_time_filter is not None:
        q = q.filter((EvidenceChunk.timestamp >= start_time_filter) | (EvidenceChunk.start_time >= start_time_filter))
    if end_time_filter is not None:
        q = q.filter((EvidenceChunk.timestamp <= end_time_filter) | (EvidenceChunk.end_time <= end_time_filter))
    
    chunks = q.all()
    if not chunks:
        return []
    
    scored = []
    for c in chunks:
        vec_score = 0.0
        if c.embedding is not None:
            try:
                # embedding stored as vector or list
                emb = c.embedding
                if isinstance(emb, str):
                    # fallback mock stored as text
                    emb = json.loads(emb) if emb.startswith("[") else None
                if emb is not None:
                    vec_score = cosine_sim(q_emb, emb)
            except Exception:
                vec_score = 0
        kw_score = keyword_score(query, c.content)
        hybrid = alpha * vec_score + (1 - alpha) * kw_score
        scored.append((hybrid, vec_score, kw_score, c))
    
    # Sort by hybrid score
    scored.sort(key=lambda x: x[0], reverse=True)
    
    # Reranking: if cross-encoder available, would rerank top N*2 ; fallback to current ordering
    # For now simple rerank boost for exact phrase
    top = scored[:top_k*2]
    # Light rerank: boost if query phrase appears
    for i, (h, v, k, c) in enumerate(top):
        if query.lower() in c.content.lower():
            top[i] = (h + 0.15, v, k, c)
    top.sort(key=lambda x: x[0], reverse=True)
    top = top[:top_k]
    
    results = []
    for hybrid, vec_score, kw_score, c in top:
        if hybrid < 0.05:  # threshold
            continue
        results.append({
            "chunk_id": c.id,
            "chunk_type": c.chunk_type,
            "content": c.content,
            "timestamp": c.timestamp,
            "start_time": c.start_time,
            "end_time": c.end_time,
            "score": round(hybrid, 4),
            "vec_score": round(vec_score, 4),
            "kw_score": round(kw_score, 4),
            "video_id": c.video_id,
            "meta": json.loads(c.meta_json) if c.meta_json else {},
        })
    return results

def build_context(chunks: List[Dict], max_tokens: int = 3000) -> str:
    # Simple context compression: truncate per chunk and concatenate with citations
    out = []
    for idx, ch in enumerate(chunks, 1):
        ts = ch.get("timestamp") or ch.get("start_time")
        ts_str = f"[{ts:.1f}s]" if ts is not None else "[unknown]"
        typ = ch["chunk_type"]
        snippet = ch["content"][:600]
        out.append(f"[{idx}] {ts_str} ({typ}): {snippet}")
    return "\n".join(out)

def evaluate_retrieval(retrieved_ids: List[str], relevant_ids: List[str], k: int = 5):
    retrieved_k = retrieved_ids[:k]
    hits = len(set(retrieved_k) & set(relevant_ids))
    precision = hits / k if k else 0
    recall = hits / len(relevant_ids) if relevant_ids else 0
    # MRR
    mrr = 0
    for rank, rid in enumerate(retrieved_k, 1):
        if rid in relevant_ids:
            mrr = 1.0 / rank
            break
    return {"precision@k": precision, "recall@k": recall, "mrr": mrr}
