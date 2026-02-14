"""Celery tasks for async document processing."""

import asyncio
import logging
from uuid import UUID

from app.services.celery_worker import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run async function in sync Celery context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def ingest_document_task(self, doc_id: str, tenant_id: str, department_id: str, file_path: str, filename: str):
    """Async task: extract, chunk, embed, and store a document."""
    try:
        _run_async(_process_document(doc_id, tenant_id, department_id, file_path, filename))
    except Exception as exc:
        logger.error(f"Document ingestion failed for {doc_id}: {exc}")
        raise self.retry(exc=exc)


async def _process_document(doc_id: str, tenant_id: str, department_id: str, file_path: str, filename: str):
    from app.db.session import async_session_factory
    from app.services.rag.ingestion import IngestionService
    from app.models.knowledge import KnowledgeDoc
    from sqlalchemy import select

    async with async_session_factory() as db:
        # Update status to processing
        result = await db.execute(select(KnowledgeDoc).where(KnowledgeDoc.id == UUID(doc_id)))
        doc = result.scalar_one_or_none()
        if not doc:
            logger.error(f"Document {doc_id} not found")
            return

        doc.status = "processing"
        await db.commit()

        try:
            ingestion = IngestionService()
            chunk_count = await ingestion.ingest_file(
                file_path=file_path,
                filename=filename,
                doc_id=UUID(doc_id),
                tenant_id=UUID(tenant_id),
                department_id=UUID(department_id),
                db=db,
            )
            doc.chunk_count = chunk_count
            doc.status = "indexed"
            await db.commit()
            logger.info(f"Document {doc_id} indexed: {chunk_count} chunks")
        except Exception as e:
            doc.status = "failed"
            await db.commit()
            raise


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def reindex_approved_answer_task(self, message_id: str, tenant_id: str, department_id: str):
    """Auto-index an approved answer into Qdrant for future retrieval."""
    try:
        _run_async(_index_approved_answer(message_id, tenant_id, department_id))
    except Exception as exc:
        logger.error(f"Reindexing failed for message {message_id}: {exc}")
        raise self.retry(exc=exc)


async def _index_approved_answer(message_id: str, tenant_id: str, department_id: str):
    from app.db.session import async_session_factory
    from app.models.conversation import Message
    from app.services.rag.embeddings import EmbeddingService
    from app.services.rag.vector_store import VectorStore
    from sqlalchemy import select

    async with async_session_factory() as db:
        result = await db.execute(select(Message).where(Message.id == UUID(message_id)))
        message = result.scalar_one_or_none()
        if not message:
            return

        embedder = EmbeddingService()
        vectors = await embedder.embed_batch([message.content])

        vector_store = VectorStore()
        await vector_store.upsert_vectors(
            ids=[message_id],
            vectors=vectors,
            payloads=[{
                "tenant_id": tenant_id,
                "department_id": department_id,
                "content": message.content,
                "source": "approved_answer",
                "message_id": message_id,
            }],
        )
        logger.info(f"Approved answer {message_id} indexed into Qdrant")
