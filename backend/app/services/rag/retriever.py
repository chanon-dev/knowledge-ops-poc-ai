from app.services.rag.embeddings import EmbeddingService
from app.services.rag.vector_store import VectorStore

VERIFIED_BOOST = 0.15


class RAGRetriever:
    """Combines embedding + vector search for RAG retrieval."""

    def __init__(self):
        self.embedder = EmbeddingService()
        self.vector_store = VectorStore()

    def retrieve(
        self,
        query: str,
        tenant_id: str,
        department_id: str,
        top_k: int = 5,
    ) -> list[dict]:
        query_vector = self.embedder.embed_text(query)

        results = self.vector_store.search(
            query_vector=query_vector,
            tenant_id=tenant_id,
            department_id=department_id,
            top_k=top_k,
        )

        # Boost verified answers so they rank higher
        for r in results:
            if r.get("source_type") == "verified_answer":
                r["score"] = min(1.0, r["score"] + VERIFIED_BOOST)

        # Re-sort by boosted score
        results.sort(key=lambda r: r["score"], reverse=True)

        # Filter out low-confidence results
        filtered = [r for r in results if r["score"] > 0.3]

        return filtered

    def build_context(
        self,
        results: list[dict],
        max_tokens: int = 2000,
    ) -> str:
        if not results:
            return ""

        verified_parts = []
        document_parts = []
        estimated_tokens = 0

        for i, r in enumerate(results):
            if r.get("source_type") == "verified_answer":
                source_text = f"[VERIFIED ANSWER (relevance: {r['score']:.2f})]\n{r['content']}"
            else:
                source_text = f"[Source {i + 1}: {r.get('title', 'Unknown')} (relevance: {r['score']:.2f})]\n{r['content']}"

            chunk_tokens = len(source_text.split()) * 1.3  # rough estimate
            if estimated_tokens + chunk_tokens > max_tokens:
                break

            if r.get("source_type") == "verified_answer":
                verified_parts.append(source_text)
            else:
                document_parts.append(source_text)
            estimated_tokens += chunk_tokens

        # Verified answers first, then document chunks
        all_parts = verified_parts + document_parts
        return "\n\n---\n\n".join(all_parts)
