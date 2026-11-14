"""
Run full eval suite against loaded DB
"""
import sys
sys.path.insert(0, "backend")
from app.db.session import SessionLocal
from app.services.rag import hybrid_search
from evals.metrics import precision_at_k, recall_at_k, mrr, latency_stats
import time

def run_rag_eval():
    db = SessionLocal()
    # Build synthetic eval set: query -> expected chunk content contains term
    test_cases = [
        {"query": "mock transcript", "expect_contains": "transcript"},
        {"query": "frame scene", "expect_contains": "frame"},
    ]
    latencies = []
    for tc in test_cases:
        start = time.time()
        # Use any video; if none, skip
        from app.models.video import Video
        v = db.query(Video).first()
        if not v:
            print("No videos for eval, skipping")
            return
        res = hybrid_search(db, str(v.id), tc["query"], top_k=5)
        lat = time.time() - start
        latencies.append(lat)
        print(f"Query '{tc['query']}' -> {len(res)} results in {lat:.3f}s")
        for r in res:
            print(f"  [{r['score']}] {r['content'][:80]}")
    print("Latency stats:", latency_stats(latencies))
    db.close()

if __name__ == "__main__":
    run_rag_eval()
