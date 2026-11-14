from typing import Dict, List
from app.services.rag import hybrid_search, build_context
from app.services.llm import get_llm_provider
from agent.state import AgentState
from agent.tools.video_tools import video_search, transcript_search, frame_analyzer, event_detector

# Lightweight LangGraph implementation with fallback if langgraph not installed
try:
    from langgraph.graph import StateGraph, END
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False
    END = "END"

# Node functions
def supervisor_node(state: AgentState) -> Dict:
    query = state["user_query"].lower()
    # Intent classification
    if any(w in query for w in ["what happened at", "timestamp", "when", "at "]):
        intent = "event"
    elif any(w in query for w in ["see", "show", "visual", "frame", "look"]):
        intent = "visual"
    elif any(w in query for w in ["summary", "summarize", "report"]):
        intent = "summary"
    elif any(w in query for w in ["who said", "transcript", "said"]):
        intent = "transcript"
    else:
        intent = "search"
    return {"intent": intent}

def retrieval_node(state: AgentState) -> Dict:
    # Use already retrieved chunks if provided, else search
    if state.get("retrieved_chunks"):
        return {}
    # Need db - will be injected via run_agent
    return {}

def vision_node(state: AgentState) -> Dict:
    # If intent visual, enrich with frame analysis
    if state.get("intent") == "visual":
        # vision observations already should be via tool
        return {"vision_observations": state.get("vision_observations", [])}
    return {}

def event_node(state: AgentState) -> Dict:
    if state.get("intent") == "event":
        return {"event_results": state.get("event_results", [])}
    return {}

def evidence_validation_node(state: AgentState) -> Dict:
    chunks = state.get("retrieved_chunks", [])
    if not chunks:
        return {"has_sufficient_evidence": False}
    # Check if top score is low
    top_score = max((c.get("score", 0) for c in chunks), default=0)
    has_sufficient = top_score > 0.15 or len(chunks) >= 2
    return {"has_sufficient_evidence": has_sufficient}

def report_node(state: AgentState) -> Dict:
    # Generation node
    chunks = state.get("retrieved_chunks", [])
    context = build_context(chunks) if chunks else "No evidence found."
    provider = get_llm_provider()
    system = "You are VisionX, evidence-grounded assistant. Cite timestamps like [12.3s]. If insufficient evidence, explicitly say so. Never fabricate."
    prompt = f"EVIDENCE:\n{context}\n\nQUESTION: {state['user_query']}\n\nProvide answer with citations."
    answer = provider.generate(prompt, system=system)
    # Determine if answer indicates insufficient evidence
    low_evidence_phrases = ["insufficient", "don't have", "no evidence", "not found"]
    has_sufficient = state.get("has_sufficient_evidence", True)
    if any(p in answer.lower() for p in low_evidence_phrases):
        has_sufficient = False
    return {"answer": answer, "has_sufficient_evidence": has_sufficient, "citations": chunks}

# Build LangGraph if available
def build_graph():
    if not HAS_LANGGRAPH:
        return None
    workflow = StateGraph(AgentState)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("vision", vision_node)
    workflow.add_node("event", event_node)
    workflow.add_node("validation", evidence_validation_node)
    workflow.add_node("report", report_node)

    workflow.set_entry_point("supervisor")
    workflow.add_edge("supervisor", "retrieval")
    # Conditional routing based on intent
    def route(state: AgentState):
        intent = state.get("intent", "search")
        if intent == "visual":
            return "vision"
        if intent == "event":
            return "event"
        return "validation"

    workflow.add_conditional_edges("retrieval", route, {"vision": "vision", "event": "event", "validation": "validation"})
    workflow.add_edge("vision", "validation")
    workflow.add_edge("event", "validation")
    workflow.add_edge("validation", "report")
    workflow.add_edge("report", END)
    return workflow.compile()

_graph = None
def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph

def run_agent(video_id: str, user_query: str, retrieved_chunks: List[Dict], db=None) -> Dict:
    # Enrich state with db tools if needed
    state: AgentState = {
        "video_id": video_id,
        "user_query": user_query,
        "intent": "",
        "retrieved_chunks": retrieved_chunks,
        "vision_observations": [],
        "event_results": [],
        "answer": "",
        "citations": retrieved_chunks,
        "has_sufficient_evidence": len(retrieved_chunks) > 0,
        "retries": 0,
        "error": None,
    }
    # Optional: if intent is visual/event, try to enrich via db
    if db is not None:
        q_lower = user_query.lower()
        try:
            if "at" in q_lower:
                # try extract time
                import re
                m = re.search(r"(\d+):(\d+)", user_query)
                if m:
                    mins, secs = int(m.group(1)), int(m.group(2))
                    ts = mins*60 + secs
                    obs = frame_analyzer(db, video_id, ts)
                    state["vision_observations"] = [obs]
            if "goal" in q_lower or "shot" in q_lower:
                evs = event_detector(db, video_id)
                state["event_results"] = evs
        except Exception as e:
            state["error"] = str(e)

    g = get_graph()
    if g is not None:
        try:
            result = g.invoke(state)
            # Ensure report node ran; if not, fallback
            if not result.get("answer"):
                fallback = report_node(result)
                result.update(fallback)
            return {"answer": result.get("answer",""), "citations": result.get("citations", retrieved_chunks), "has_sufficient_evidence": result.get("has_sufficient_evidence", True)}
        except Exception as e:
            # Fallback to simple
            out = report_node(state)
            return {"answer": out["answer"], "citations": out["citations"], "has_sufficient_evidence": out["has_sufficient_evidence"] }
    else:
        # No langgraph, direct
        # Run sequential nodes
        s = supervisor_node(state)
        state.update(s)
        v = evidence_validation_node(state)
        state.update(v)
        r = report_node(state)
        state.update(r)
        return {"answer": state["answer"], "citations": state["citations"], "has_sufficient_evidence": state["has_sufficient_evidence"]}
