from pydantic import BaseModel


class DailyUsage(BaseModel):
    date: str
    queries: int


class DepartmentUsage(BaseModel):
    department: str
    queries: int


class UsageOverview(BaseModel):
    total_queries: int
    active_users: int
    queries_per_day: list[DailyUsage]
    by_department: list[DepartmentUsage]


class DepartmentStats(BaseModel):
    total_queries: int
    avg_confidence: float
    approval_rate: float
    total_approvals: int
    approved: int


class ConfidenceTrendItem(BaseModel):
    date: str
    avg_confidence: float
    avg_latency: float


class AIPerformance(BaseModel):
    avg_latency_ms: float
    confidence_trend: list[ConfidenceTrendItem]
    total_tokens_input: int
    total_tokens_output: int
