import time
import asyncio
import logging
from typing import TypedDict
from uuid import UUID

from langgraph.graph import END, StateGraph

from app.core.config import settings

logger = logging.getLogger(__name__)


class QueryState(TypedDict):
    query: str
    department_id: str
    tenant_id: str
    user_id: str
    image_path: str | None
    # Department config
    department_config: dict
    model_name: str
    confidence_threshold: float
    system_prompt: str
    # Vision
    image_description: str | None
    # RAG results
    rag_results: list[dict]
    context: str
    # LLM output
    answer: str
    confidence: float
    sources: list[dict]
    model_used: str
    tokens_input: int
    tokens_output: int
    latency_ms: float
    # Routing
    needs_approval: bool
    approval_id: str | None
    error: str | None


def receive_query(state: QueryState) -> dict:
    """Parse and validate the incoming query."""
    return {"error": None, "image_description": None, "approval_id": None}


def route_department(state: QueryState) -> dict:
    """Load department configuration."""
    config = state.get("department_config", {})
    return {
        "model_name": settings.OLLAMA_MODEL,
        "confidence_threshold": config.get("confidence_threshold", 0.85),
        "system_prompt": config.get(
            "system_prompt",
            "You are a helpful AI assistant.",
        ),
    }


def process_vision(state: QueryState) -> dict:
    """Process image through vision pipeline if image is attached."""
    image_path = state.get("image_path")
    if not image_path:
        return {"image_description": None}

    try:
        from ml.vision.image_processor import ImageProcessor
        processor = ImageProcessor()

        loop = asyncio.new_event_loop()
        try:
            description = loop.run_until_complete(
                processor.analyze_screenshot(image_path, state["query"])
            )
        finally:
            loop.close()

        return {"image_description": description}
    except Exception as e:
        logger.warning(f"Vision processing failed: {e}")
        return {"image_description": f"[Image attached but could not be processed: {e}]"}


def rag_search(state: QueryState) -> dict:
    """Execute RAG retrieval (synchronous wrapper)."""
    from app.services.rag.retriever import RAGRetriever

    try:
        retriever = RAGRetriever()
        results = retriever.retrieve(
            query=state["query"],
            tenant_id=state["tenant_id"],
            department_id=state["department_id"],
            top_k=5,
        )
        context = retriever.build_context(results, max_tokens=2000)

        # Append vision description to context if available
        image_desc = state.get("image_description")
        if image_desc:
            context += f"\n\n[Image Analysis]\n{image_desc}"

        sources = [
            {
                "title": r.get("title", "Unknown"),
                "chunk": r.get("content", "")[:200],
                "score": r.get("score", 0),
                "document_id": r.get("document_id"),
            }
            for r in results
        ]
        return {"rag_results": results, "context": context, "sources": sources}
    except Exception as e:
        return {"rag_results": [], "context": "", "sources": [], "error": str(e)}


def generate_answer(state: QueryState) -> dict:
    """Call LLM with RAG context to generate answer."""
    from app.services.llm.ollama_client import OllamaClient
    from app.services.llm.prompt_templates import build_rag_prompt

    messages = build_rag_prompt(
        query=state["query"],
        context=state.get("context", ""),
        system_prompt=state.get("system_prompt", "You are a helpful AI assistant."),
    )

    model = state.get("model_name", settings.OLLAMA_MODEL)
    client = OllamaClient()

    start = time.perf_counter()
    try:
        loop = asyncio.new_event_loop()
        try:
            answer = loop.run_until_complete(client.chat(messages, model=model))
        finally:
            loop.close()
    except Exception as e:
        return {
            "answer": f"I apologize, but I encountered an error generating a response: {e}",
            "confidence": 0.0,
            "model_used": model,
            "latency_ms": (time.perf_counter() - start) * 1000,
            "error": str(e),
        }

    latency_ms = (time.perf_counter() - start) * 1000
    tokens_input = sum(len(m.get("content", "").split()) for m in messages)
    tokens_output = len(answer.split())

    return {
        "answer": answer,
        "model_used": model,
        "tokens_input": int(tokens_input * 1.3),
        "tokens_output": int(tokens_output * 1.3),
        "latency_ms": latency_ms,
    }


def confidence_check(state: QueryState) -> dict:
    """Evaluate answer confidence and determine if approval is needed."""
    threshold = state.get("confidence_threshold", 0.85)

    answer = state.get("answer", "")
    sources = state.get("sources", [])
    rag_results = state.get("rag_results", [])

    confidence = 0.5

    if rag_results:
        max_score = max((r.get("score", 0) for r in rag_results), default=0)
        confidence += max_score * 0.3

    if len(answer) > 100:
        confidence += 0.1

    uncertainty_phrases = ["i'm not sure", "i don't know", "unclear", "cannot determine"]
    if any(phrase in answer.lower() for phrase in uncertainty_phrases):
        confidence -= 0.2

    confidence = max(0.0, min(1.0, confidence))
    needs_approval = confidence < threshold

    return {
        "confidence": round(confidence, 3),
        "needs_approval": needs_approval,
    }


def escalate_to_human(state: QueryState) -> dict:
    """Create an approval ticket when confidence is below threshold."""
    # The actual approval creation is handled by query_service when it detects needs_approval
    logger.info(
        f"Escalating to human: confidence={state.get('confidence')}, "
        f"threshold={state.get('confidence_threshold')}"
    )
    return {"needs_approval": True}


def return_answer(state: QueryState) -> dict:
    """Format and return the final response."""
    return state


# --- Edge conditions ---

def should_process_vision(state: QueryState) -> str:
    if state.get("image_path"):
        return "has_image"
    return "text_only"


def should_approve(state: QueryState) -> str:
    if state.get("needs_approval", False):
        return "needs_approval"
    return "auto_approved"


def create_query_graph() -> StateGraph:
    """Create and return the compiled query processing graph."""
    workflow = StateGraph(QueryState)

    # Add nodes
    workflow.add_node("receive_query", receive_query)
    workflow.add_node("route_department", route_department)
    workflow.add_node("process_vision", process_vision)
    workflow.add_node("rag_search", rag_search)
    workflow.add_node("generate_answer", generate_answer)
    workflow.add_node("confidence_check", confidence_check)
    workflow.add_node("escalate_to_human", escalate_to_human)
    workflow.add_node("return_answer", return_answer)

    # Add edges
    workflow.set_entry_point("receive_query")
    workflow.add_edge("receive_query", "route_department")

    # Conditional: vision or skip
    workflow.add_conditional_edges(
        "route_department",
        should_process_vision,
        {"has_image": "process_vision", "text_only": "rag_search"},
    )
    workflow.add_edge("process_vision", "rag_search")
    workflow.add_edge("rag_search", "generate_answer")
    workflow.add_edge("generate_answer", "confidence_check")

    # Conditional: approval or direct return
    workflow.add_conditional_edges(
        "confidence_check",
        should_approve,
        {"needs_approval": "escalate_to_human", "auto_approved": "return_answer"},
    )
    workflow.add_edge("escalate_to_human", "return_answer")
    workflow.add_edge("return_answer", END)

    return workflow.compile()
