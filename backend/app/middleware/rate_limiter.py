from datetime import date

import redis.asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings


PLAN_LIMITS = {
    "free": settings.RATE_LIMIT_FREE,
    "professional": settings.RATE_LIMIT_PRO,
    "enterprise": settings.RATE_LIMIT_ENTERPRISE,
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_url: str):
        super().__init__(app)
        self.redis = aioredis.from_url(redis_url, decode_responses=True)

    async def dispatch(self, request: Request, call_next):
        tenant_id = getattr(request.state, "tenant_id", None)
        if not tenant_id:
            return await call_next(request)

        # Only rate-limit query endpoints (POST to /query or /chat)
        if request.method != "POST" or "/query" not in request.url.path:
            return await call_next(request)

        today = date.today().isoformat()
        key = f"quota:{tenant_id}:{today}"

        try:
            current = await self.redis.incr(key)
            if current == 1:
                await self.redis.expire(key, 86400)

            plan_tier = getattr(request.state, "plan_tier", "free")
            limit = PLAN_LIMITS.get(plan_tier, settings.RATE_LIMIT_FREE)

            if limit > 0 and current > limit:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "DAILY_QUOTA_EXCEEDED",
                            "message": f"Daily quota exceeded ({current}/{limit}). Upgrade your plan for higher limits.",
                        }
                    },
                    headers={
                        "Retry-After": "86400",
                        "X-Quota-Limit": str(limit),
                        "X-Quota-Used": str(current),
                    },
                )

            response = await call_next(request)
            response.headers["X-Quota-Limit"] = str(limit)
            response.headers["X-Quota-Used"] = str(current)
            return response
        except Exception:
            # If Redis is down, allow the request through
            return await call_next(request)
