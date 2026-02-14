import os
import tempfile
from uuid import UUID

from minio import Minio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.models.knowledge import KnowledgeChunk, KnowledgeDoc
from app.services.rag.ingestion import IngestionService
from app.services.rag.vector_store import VectorStore


class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.minio_client = Minio(
            getattr(settings, "MINIO_ENDPOINT", "localhost:9000"),
            access_key=getattr(settings, "MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=getattr(settings, "MINIO_SECRET_KEY", "minioadmin"),
            secure=False,
        )
        self.bucket = "knowledge-docs"

    async def upload_document(
        self,
        tenant_id: UUID,
        department_id: UUID,
        user_id: UUID,
        file_content: bytes,
        filename: str,
        title: str,
        mime_type: str,
    ) -> KnowledgeDoc:
        # Store file in MinIO
        object_name = f"tenant-{tenant_id}/dept-{department_id}/{filename}"
        if not self.minio_client.bucket_exists(self.bucket):
            self.minio_client.make_bucket(self.bucket)

        import io
        self.minio_client.put_object(
            self.bucket,
            object_name,
            io.BytesIO(file_content),
            len(file_content),
            content_type=mime_type,
        )

        # Determine source type from extension
        ext = os.path.splitext(filename)[1].lower().lstrip(".")
        source_type = ext if ext in ("pdf", "docx", "txt", "md", "csv", "html") else "manual"

        # Create DB record
        doc = KnowledgeDoc(
            tenant_id=tenant_id,
            department_id=department_id,
            uploaded_by=user_id,
            title=title,
            source_type=source_type,
            file_path=object_name,
            mime_type=mime_type,
            file_size=len(file_content),
            status="pending",
        )
        self.db.add(doc)
        await self.db.flush()
        await self.db.refresh(doc)

        # Trigger async ingestion (in a real app, use Celery)
        try:
            # Save to temp file for extraction
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                tmp.write(file_content)
                tmp_path = tmp.name

            ingestion = IngestionService(self.db)
            await ingestion.ingest_document(
                doc_id=doc.id,
                tenant_id=tenant_id,
                department_id=department_id,
                file_path=tmp_path,
                mime_type=mime_type,
            )
        except Exception:
            # Ingestion failure is non-blocking; status is set in ingestion service
            pass
        finally:
            if "tmp_path" in locals():
                os.unlink(tmp_path)

        await self.db.refresh(doc)
        return doc

    async def list_documents(
        self,
        tenant_id: UUID,
        department_id: UUID,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[KnowledgeDoc], int]:
        base = select(KnowledgeDoc).where(
            KnowledgeDoc.tenant_id == tenant_id,
            KnowledgeDoc.department_id == department_id,
            KnowledgeDoc.deleted_at.is_(None),
        )
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = (
            base.order_by(KnowledgeDoc.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def get_document(self, doc_id: UUID) -> KnowledgeDoc:
        stmt = select(KnowledgeDoc).where(
            KnowledgeDoc.id == doc_id,
            KnowledgeDoc.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        doc = result.scalar_one_or_none()
        if not doc:
            raise NotFoundError(f"Document {doc_id} not found")
        return doc

    async def delete_document(self, doc_id: UUID) -> None:
        doc = await self.get_document(doc_id)

        # Delete vectors from Qdrant
        try:
            vs = VectorStore()
            vs.delete_by_document(str(doc_id))
        except Exception:
            pass

        # Delete file from MinIO
        try:
            if doc.file_path:
                self.minio_client.remove_object(self.bucket, doc.file_path)
        except Exception:
            pass

        # Soft delete
        doc.deleted_at = func.now()
        await self.db.flush()
