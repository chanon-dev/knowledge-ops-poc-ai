"""Airflow DAG: Nightly data consistency check and weekly archival."""

import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/the_expert")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

default_args = {
    "owner": "the-expert",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def consistency_check(**context):
    """Verify PostgreSQL knowledge chunks are in sync with Qdrant vectors."""
    from sqlalchemy import create_engine, text
    from qdrant_client import QdrantClient

    engine = create_engine(DB_URL)
    qdrant = QdrantClient(url=QDRANT_URL)

    with engine.connect() as conn:
        result = conn.execute(text("SELECT id FROM knowledge_chunks WHERE status = 'active'"))
        pg_ids = {str(row[0]) for row in result}

    collection_info = qdrant.get_collection("knowledge_chunks")
    qdrant_count = collection_info.points_count

    report = {
        "pg_chunk_count": len(pg_ids),
        "qdrant_vector_count": qdrant_count,
        "in_sync": len(pg_ids) == qdrant_count,
    }
    context["ti"].xcom_push(key="consistency_report", value=report)

    if not report["in_sync"]:
        diff = abs(len(pg_ids) - qdrant_count)
        if diff > 100:
            raise ValueError(f"Large sync discrepancy: PG={len(pg_ids)}, Qdrant={qdrant_count}")


def archive_old_data(**context):
    """Archive conversations and audit logs older than retention period."""
    from sqlalchemy import create_engine, text

    engine = create_engine(DB_URL)
    retention_days = 365

    with engine.connect() as conn:
        result = conn.execute(text(f"""
            DELETE FROM messages WHERE conversation_id IN (
                SELECT id FROM conversations
                WHERE updated_at < NOW() - INTERVAL '{retention_days} days'
            )
        """))
        deleted_messages = result.rowcount

        result = conn.execute(text(f"""
            DELETE FROM conversations
            WHERE updated_at < NOW() - INTERVAL '{retention_days} days'
        """))
        deleted_convos = result.rowcount

        result = conn.execute(text(f"""
            DELETE FROM audit_logs
            WHERE created_at < NOW() - INTERVAL '{retention_days * 2} days'
        """))
        deleted_logs = result.rowcount

        conn.commit()

    report = {
        "deleted_messages": deleted_messages,
        "deleted_conversations": deleted_convos,
        "deleted_audit_logs": deleted_logs,
    }
    context["ti"].xcom_push(key="archive_report", value=report)


def vacuum_db(**context):
    """Run VACUUM ANALYZE on key tables after archival."""
    from sqlalchemy import create_engine, text

    engine = create_engine(DB_URL)
    tables = ["messages", "conversations", "audit_logs", "usage_records"]
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        for table in tables:
            conn.execute(text(f"VACUUM ANALYZE {table}"))


with DAG(
    "data_pipeline",
    default_args=default_args,
    description="Nightly consistency check and weekly data archival",
    schedule_interval="0 2 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["data", "maintenance"],
) as dag:

    check = PythonOperator(task_id="consistency_check", python_callable=consistency_check)
    archive = PythonOperator(task_id="archive_old_data", python_callable=archive_old_data)
    vacuum = PythonOperator(task_id="vacuum_db", python_callable=vacuum_db)

    check >> archive >> vacuum
