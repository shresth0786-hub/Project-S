import hashlib
import numpy as np
from typing import List
from app.core.config import settings

_model = None
_use_mock = False

def get_embedding_model():
    global _model, _use_mock
    if _model is not None or _use_mock:
        return _model
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return _model
    except Exception as e:
        print(f"[embeddings] Failed to load model {settings.EMBEDDING_MODEL}: {e}. Using mock embeddings.")
        _use_mock = True
        return None

def mock_embedding(text: str, dim: int = 384) -> List[float]:
    # Deterministic mock based on hash
    h = hashlib.sha256(text.encode()).digest()
    # Expand to dim
    vals = []
    for i in range(dim):
        vals.append(((h[i % len(h)] / 255.0) * 2 - 1) * 0.1)
    # Normalize
    arr = np.array(vals, dtype=np.float32)
    norm = np.linalg.norm(arr)
    if norm > 0:
        arr = arr / norm
    return arr.tolist()

def embed_text(text: str) -> List[float]:
    model = get_embedding_model()
    if model is None:
        return mock_embedding(text, settings.EMBEDDING_DIM)
    try:
        vec = model.encode(text, normalize_embeddings=True)
        return vec.tolist()
    except Exception as e:
        print(f"Embedding error: {e}, fallback to mock")
        return mock_embedding(text, settings.EMBEDDING_DIM)

def embed_batch(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    model = get_embedding_model()
    if model is None:
        return [mock_embedding(t, settings.EMBEDDING_DIM) for t in texts]
    try:
        vecs = model.encode(texts, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=False)
        return [v.tolist() for v in vecs]
    except Exception as e:
        print(f"Batch embedding error: {e}")
        return [mock_embedding(t, settings.EMBEDDING_DIM) for t in texts]
