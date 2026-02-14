"""
Initialize MinIO buckets for the application.

Creates the following default buckets (if they do not already exist):
  - knowledge-docs   : uploaded knowledge-base documents (PDF, DOCX, etc.)
  - user-uploads      : user-submitted files and images
  - model-artifacts   : serialised model weights / config snapshots

Usage:
    python -m scripts.init_minio                          # defaults
    python -m scripts.init_minio --endpoint minio.local:9000 --access-key admin --secret-key admin123
"""

from __future__ import annotations

import argparse
import os
import sys

from minio import Minio

DEFAULT_BUCKETS = [
    "knowledge-docs",
    "user-uploads",
    "model-artifacts",
]


def ensure_buckets(client: Minio, buckets: list[str]) -> None:
    """Create each bucket if it does not already exist."""

    for bucket_name in buckets:
        if client.bucket_exists(bucket_name):
            print(f"[skip] Bucket '{bucket_name}' already exists.")
        else:
            client.make_bucket(bucket_name)
            print(f"[ok]   Bucket '{bucket_name}' created.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize MinIO buckets")
    parser.add_argument(
        "--endpoint",
        default=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        help="MinIO endpoint (default: localhost:9000 or $MINIO_ENDPOINT)",
    )
    parser.add_argument(
        "--access-key",
        default=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        help="MinIO access key (default: minioadmin or $MINIO_ACCESS_KEY)",
    )
    parser.add_argument(
        "--secret-key",
        default=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        help="MinIO secret key (default: minioadmin or $MINIO_SECRET_KEY)",
    )
    parser.add_argument(
        "--secure",
        action="store_true",
        default=False,
        help="Use HTTPS (default: False)",
    )
    args = parser.parse_args()

    print(f"Connecting to MinIO at {args.endpoint} ...")
    client = Minio(
        endpoint=args.endpoint,
        access_key=args.access_key,
        secret_key=args.secret_key,
        secure=args.secure,
    )

    try:
        ensure_buckets(client, DEFAULT_BUCKETS)
        print("\nMinIO initialization complete.")
    except Exception as exc:
        print(f"\n[error] Failed to initialize MinIO: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
