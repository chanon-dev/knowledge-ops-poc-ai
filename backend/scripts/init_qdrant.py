"""
Initialize Qdrant collection for knowledge vector storage.

Creates the 'knowledge_vectors' collection with:
  - Vector size 1024 (BGE-large-en-v1.5 embedding dimension)
  - Cosine distance metric
  - Payload indexes for tenant_id, department_id, document_id, chunk_index

Usage:
    python -m scripts.init_qdrant          # uses default localhost:6333
    python -m scripts.init_qdrant --host qdrant.example.com --port 6333
"""

from __future__ import annotations

import argparse
import sys

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PayloadSchemaType,
)

COLLECTION_NAME = "knowledge_vectors"
VECTOR_SIZE = 1024  # BGE-large-en-v1.5


def create_collection(client: QdrantClient) -> None:
    """Create the knowledge_vectors collection if it does not already exist."""

    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME in existing:
        print(f"[skip] Collection '{COLLECTION_NAME}' already exists.")
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )
    print(f"[ok]   Collection '{COLLECTION_NAME}' created (vector_size={VECTOR_SIZE}, distance=Cosine).")


def create_payload_indexes(client: QdrantClient) -> None:
    """Create payload indexes for efficient multi-tenant filtering."""

    indexes: list[tuple[str, PayloadSchemaType]] = [
        ("tenant_id", PayloadSchemaType.KEYWORD),
        ("department_id", PayloadSchemaType.KEYWORD),
        ("document_id", PayloadSchemaType.KEYWORD),
        ("chunk_index", PayloadSchemaType.INTEGER),
    ]

    for field_name, schema_type in indexes:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name=field_name,
            field_schema=schema_type,
        )
        print(f"[ok]   Payload index created: {field_name} ({schema_type.value})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize Qdrant knowledge_vectors collection")
    parser.add_argument("--host", default="localhost", help="Qdrant host (default: localhost)")
    parser.add_argument("--port", type=int, default=6333, help="Qdrant gRPC/HTTP port (default: 6333)")
    args = parser.parse_args()

    print(f"Connecting to Qdrant at {args.host}:{args.port} ...")
    client = QdrantClient(host=args.host, port=args.port)

    try:
        create_collection(client)
        create_payload_indexes(client)
        print("\nQdrant initialization complete.")
    except Exception as exc:
        print(f"\n[error] Failed to initialize Qdrant: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
