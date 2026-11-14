from typing import List, Dict, Optional, TypedDict, Annotated
from uuid import UUID

class AgentState(TypedDict):
    video_id: str
    user_query: str
    intent: str  # search, summary, event, visual, report
    retrieved_chunks: List[Dict]
    vision_observations: List[Dict]
    event_results: List[Dict]
    answer: str
    citations: List[Dict]
    has_sufficient_evidence: bool
    retries: int
    error: Optional[str]
