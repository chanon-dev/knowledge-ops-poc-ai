from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger


class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: list | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found", details: list | None = None):
        super().__init__(code="NOT_FOUND", message=message, status_code=404, details=details)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Authentication required", details: list | None = None):
        super().__init__(code="UNAUTHORIZED", message=message, status_code=401, details=details)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Insufficient permissions", details: list | None = None):
        super().__init__(code="FORBIDDEN", message=message, status_code=403, details=details)


class BadRequestError(AppException):
    def __init__(self, message: str = "Bad request", details: list | None = None):
        super().__init__(code="BAD_REQUEST", message=message, status_code=400, details=details)


class ConflictError(AppException):
    def __init__(self, message: str = "Resource already exists", details: list | None = None):
        super().__init__(code="CONFLICT", message=message, status_code=409, details=details)


class RateLimitExceededError(AppException):
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(code="RATE_LIMIT_EXCEEDED", message=message, status_code=429)
        self.retry_after = retry_after


def _build_error_body(exc: AppException, request_id: str | None = None) -> dict:
    body: dict = {
        "error": {
            "code": exc.code,
            "message": exc.message,
        }
    }
    if exc.details:
        body["error"]["details"] = exc.details
    if request_id:
        body["error"]["request_id"] = request_id
    return body


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        headers = {}
        if isinstance(exc, RateLimitExceededError):
            headers["Retry-After"] = str(exc.retry_after)
        return JSONResponse(
            status_code=exc.status_code,
            content=_build_error_body(exc, request_id),
            headers=headers,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.exception("Unhandled exception: {}", str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "request_id": request_id,
                }
            },
        )
