from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.security import decode_jwt


SKIP_PATHS = frozenset({
    "/",
    "/health",
    "/api/v1/health",
    "/api/v1/health/ready",
    "/api/v1/docs",
    "/api/v1/redoc",
    "/api/v1/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
})


class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in SKIP_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return await call_next(request)

        try:
            parts = auth_header.split(" ", 1)
            if len(parts) != 2:
                return await call_next(request)

            scheme, token = parts
            if scheme.lower() == "bearer":
                payload = decode_jwt(token)
                request.state.tenant_id = payload.get("tenant_id")
                request.state.user_id = payload.get("sub")
                request.state.user_role = payload.get("role", "viewer")
                request.state.user_email = payload.get("email")
        except Exception:
            # Let the auth dependency handle the actual 401 response
            pass

        return await call_next(request)
