from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    Filter,
    FieldCondition,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.core.config import settings

COLLECTION_NAME = "knowledge_vectors"
VECTOR_SIZE = 1024  # BGE-large-en-v1.5


class VectorStore:
    """Qdrant vector store for knowledge retrieval."""

    def __init__(self, url: str | None = None):
        url = url or settings.QDRANT_URL
        self.client = QdrantClient(url=url, timeout=30)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        collections = self.client.get_collections().collections
        names = [c.name for c in collections]
        if COLLECTION_NAME not in names:
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
            self.client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="tenant_id",
                field_schema="keyword",
            )
            self.client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="department_id",
                field_schema="keyword",
            )
            self.client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="document_id",
                field_schema="keyword",
            )
            self.client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="source_type",
                field_schema="keyword",
            )

    def upsert_vectors(self, points: list[dict]) -> None:
        qdrant_points = []
        for p in points:
            point_id = p.get("id", str(uuid4()))
            qdrant_points.append(
                PointStruct(
                    id=point_id,
                    vector=p["vector"],
                    payload={
                        "tenant_id": str(p["tenant_id"]),
                        "department_id": str(p["department_id"]),
                        "document_id": str(p["document_id"]),
                        "chunk_index": p.get("chunk_index", 0),
                        "content": p.get("content", "")[:500],
                        "title": p.get("title", ""),
                        "source_type": p.get("source_type", "document"),
                    },
                )
            )

        batch_size = 100
        for i in range(0, len(qdrant_points), batch_size):
            batch = qdrant_points[i : i + batch_size]
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=batch,
            )

    def search(
        self,
        query_vector: list[float],
        tenant_id: str,
        department_id: str,
        top_k: int = 5,
    ) -> list[dict]:
        results = self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="tenant_id",
                        match=MatchValue(value=str(tenant_id)),
                    ),
                    FieldCondition(
                        key="department_id",
                        match=MatchValue(value=str(department_id)),
                    ),
                ]
            ),
            limit=top_k,
        )

        return [
            {
                "id": str(r.id),
                "score": r.score,
                "content": r.payload.get("content", ""),
                "title": r.payload.get("title", ""),
                "document_id": r.payload.get("document_id"),
                "chunk_index": r.payload.get("chunk_index", 0),
                "source_type": r.payload.get("source_type", "document"),
            }
            for r in results
        ]

    def delete_by_document(self, document_id: str) -> None:
        self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=str(document_id)),
                    ),
                ]
            ),
        )
