from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeChunk, KnowledgeDoc
from app.services.rag.chunker import TextChunker
from app.services.rag.embeddings import EmbeddingService
from app.services.rag.extractor import DocumentExtractor
from app.services.rag.vector_store import VectorStore


class IngestionService:
    """Full document ingestion pipeline: extract -> chunk -> embed -> store."""

    def __init__(self, db: AsyncSession, qdrant_url: str = "http://localhost:6333"):
        self.db = db
        self.extractor = DocumentExtractor()
        self.chunker = TextChunker()
        self.embedder = EmbeddingService()
        self.vector_store = VectorStore(url=qdrant_url)

    async def ingest_document(
        self,
        doc_id: UUID,
        tenant_id: UUID,
        department_id: UUID,
        file_path: str,
        mime_type: str,
    ) -> None:
        # Get the document record
        stmt = select(KnowledgeDoc).where(KnowledgeDoc.id == doc_id)
        result = await self.db.execute(stmt)
        doc = result.scalar_one_or_none()
        if not doc:
            raise ValueError(f"Document {doc_id} not found")

        try:
            # Update status to processing
            doc.status = "processing"
            await self.db.flush()

            # 1. Extract text
            text = self.extractor.extract(file_path, mime_type)
            if not text.strip():
                doc.status = "failed"
                doc.metadata_ = {**doc.metadata_, "error": "No text content extracted"}
                await self.db.flush()
                return

            # 2. Chunk text
            chunks = self.chunker.chunk_document(
                text,
                metadata={
                    "document_id": str(doc_id),
                    "tenant_id": str(tenant_id),
                    "department_id": str(department_id),
                    "title": doc.title,
                },
            )

            if not chunks:
                doc.status = "failed"
                doc.metadata_ = {**doc.metadata_, "error": "No chunks generated"}
                await self.db.flush()
                return

            # 3. Generate embeddings
            texts = [c["content"] for c in chunks]
            embeddings = self.embedder.embed_batch(texts)

            # 4. Store in Qdrant
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point_id = str(uuid4())
                points.append(
                    {
                        "id": point_id,
                        "vector": embedding,
                        "tenant_id": str(tenant_id),
                        "department_id": str(department_id),
                        "document_id": str(doc_id),
                        "chunk_index": i,
                        "content": chunk["content"],
                        "title": doc.title,
                    }
                )

            self.vector_store.upsert_vectors(points)

            # 5. Store chunks in PostgreSQL
            for i, (chunk, point) in enumerate(zip(chunks, points)):
                db_chunk = KnowledgeChunk(
                    document_id=doc_id,
                    tenant_id=tenant_id,
                    department_id=department_id,
                    chunk_index=i,
                    content=chunk["content"],
                    qdrant_point_id=point["id"],
                    token_count=chunk.get("token_count", 0),
                    metadata_=chunk.get("metadata", {}),
                )
                self.db.add(db_chunk)

            # 6. Update document status
            doc.status = "indexed"
            doc.chunk_count = len(chunks)
            await self.db.flush()

        except Exception as e:
            doc.status = "failed"
            doc.metadata_ = {**doc.metadata_, "error": str(e)}
            await self.db.flush()
            raise
