"""
VisionX Evaluation Framework
Measures RAG, latency, sports event accuracy.
Usage: python evals/metrics.py --run
"""
from typing import List, Dict
import time
import statistics

def precision_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
    retrieved_k = retrieved[:k]
    hits = len(set(retrieved_k) & set(relevant))
    return hits / k if k else 0

def recall_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
    retrieved_k = retrieved[:k]
    hits = len(set(retrieved_k) & set(relevant))
    return hits / len(relevant) if relevant else 0

def mrr(retrieved: List[str], relevant: List[str]) -> float:
    for rank, doc in enumerate(retrieved, 1):
        if doc in relevant:
            return 1.0 / rank
    return 0.0

def citation_correctness(generated_citations: List[Dict], ground_truth: List[Dict]) -> float:
    if not generated_citations:
        return 0
    correct = sum(1 for c in generated_citations if any(abs((c.get("timestamp") or 0) - (g.get("timestamp") or 0)) < 2.0 for g in ground_truth))
    return correct / len(generated_citations)

def latency_stats(latencies: List[float]) -> Dict:
    if not latencies:
        return {}
    latencies.sort()
    return {
        "p50": statistics.median(latencies),
        "p95": latencies[int(0.95*len(latencies))],
        "mean": statistics.mean(latencies),
        "min": min(latencies),
        "max": max(latencies),
    }

def sports_metrics(tp: int, fp: int, fn: int):
    precision = tp / (tp+fp) if tp+fp else 0
    recall = tp / (tp+fn) if tp+fn else 0
    f1 = 2*precision*recall/(precision+recall) if precision+recall else 0
    return {"precision": precision, "recall": recall, "f1": f1}

def timestamp_error(pred: float, gt: float) -> float:
    return abs(pred - gt)

if __name__ == "__main__":
    # Demo with synthetic data
    retrieved = ["a","b","c","d","e"]
    relevant = ["b","d","x"]
    print("P@3", precision_at_k(retrieved, relevant, 3))
    print("R@3", recall_at_k(retrieved, relevant, 3))
    print("MRR", mrr(retrieved, relevant))
    print("latency", latency_stats([0.12,0.15,0.2,0.3,0.9,1.2]))
    print("sports", sports_metrics(8,2,3))
