from app.services.rag.embeddings import EmbeddingService
from app.services.rag.vector_store import VectorStore


class RAGRetriever:
    """Combines embedding + vector search for RAG retrieval."""

    def __init__(self, qdrant_url: str = "http://localhost:6333"):
        self.embedder = EmbeddingService()
        self.vector_store = VectorStore(url=qdrant_url)

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

        # Simple reranking: results are already sorted by score from Qdrant
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

        context_parts = []
        estimated_tokens = 0

        for i, r in enumerate(results):
            source_text = f"[Source {i + 1}: {r.get('title', 'Unknown')} (relevance: {r['score']:.2f})]\n{r['content']}"
            chunk_tokens = len(source_text.split()) * 1.3  # rough estimate
            if estimated_tokens + chunk_tokens > max_tokens:
                break
            context_parts.append(source_text)
            estimated_tokens += chunk_tokens

        return "\n\n---\n\n".join(context_parts)
