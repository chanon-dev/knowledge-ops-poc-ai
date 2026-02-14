"""Caching service using Redis for query results, RAG, and embeddings."""

import hashlib
import json
import logging
from typing import Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching for query results, RAG, and embeddings."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis = redis.from_url(redis_url, decode_responses=True)

    def _key(self, prefix: str, *parts: str) -> str:
        raw = ":".join(parts)
        hashed = hashlib.md5(raw.encode()).hexdigest()
        return f"cache:{prefix}:{hashed}"

    # --- Query Result Cache (1-hour TTL) ---

    async def get_query_cache(self, tenant_id: str, department_id: str, query: str) -> Optional[dict]:
        key = self._key("query", tenant_id, department_id, query.lower().strip())
        data = await self.redis.get(key)
        if data:
            logger.debug(f"Query cache HIT: {key}")
            return json.loads(data)
        return None

    async def set_query_cache(self, tenant_id: str, department_id: str, query: str, result: dict, ttl: int = 3600):
        key = self._key("query", tenant_id, department_id, query.lower().strip())
        await self.redis.set(key, json.dumps(result, default=str), ex=ttl)

    async def invalidate_query_cache(self, tenant_id: str, department_id: str):
        """Invalidate all query caches for a department (e.g., after knowledge base update)."""
        pattern = f"cache:query:{hashlib.md5(tenant_id.encode()).hexdigest()[:8]}*"
        async for key in self.redis.scan_iter(match=pattern, count=100):
            await self.redis.delete(key)

    # --- RAG Result Cache (department-scoped, 30-min TTL) ---

    async def get_rag_cache(self, tenant_id: str, department_id: str, query: str) -> Optional[list]:
        key = self._key("rag", tenant_id, department_id, query.lower().strip())
        data = await self.redis.get(key)
        if data:
            logger.debug(f"RAG cache HIT: {key}")
            return json.loads(data)
        return None

    async def set_rag_cache(self, tenant_id: str, department_id: str, query: str, results: list, ttl: int = 1800):
        key = self._key("rag", tenant_id, department_id, query.lower().strip())
        await self.redis.set(key, json.dumps(results, default=str), ex=ttl)

    # --- Embedding Cache (avoid re-embedding same documents) ---

    async def get_embedding_cache(self, text_hash: str) -> Optional[list[float]]:
        key = f"cache:embed:{text_hash}"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def set_embedding_cache(self, text_hash: str, embedding: list[float], ttl: int = 86400):
        key = f"cache:embed:{text_hash}"
        await self.redis.set(key, json.dumps(embedding), ex=ttl)

    # --- General cache operations ---

    async def clear_all(self, prefix: str = "cache:*"):
        async for key in self.redis.scan_iter(match=prefix, count=100):
            await self.redis.delete(key)

    async def close(self):
        await self.redis.close()
