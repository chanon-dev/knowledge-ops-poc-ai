import math
from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int
    per_page: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    pagination: PaginationMeta


class ErrorDetail(BaseModel):
    field: str | None = None
    reason: str


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] | None = None
    request_id: str | None = None


class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(20, ge=1, le=100, description="Items per page"),
        sort: str = Query("created_at", description="Sort field"),
        order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    ):
        self.page = page
        self.per_page = per_page
        self.sort = sort
        self.order = order

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page


def build_paginated_response(
    items: list,
    total: int,
    pagination: PaginationParams,
    schema_class: type | None = None,
) -> dict:
    total_pages = math.ceil(total / pagination.per_page) if pagination.per_page > 0 else 0
    data = items
    if schema_class:
        data = [schema_class.model_validate(item) for item in items]
    return {
        "data": data,
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_items": total,
            "total_pages": total_pages,
            "has_next": pagination.page < total_pages,
            "has_prev": pagination.page > 1,
        },
    }
