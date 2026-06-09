"""监控源 — Pydantic 模型"""

from pydantic import BaseModel, Field


class MonitorSourceCreate(BaseModel):
    path: str = Field(..., min_length=1)
    label: str = ""
    enabled: bool = True


class MonitorSourceUpdate(BaseModel):
    label: str | None = None
    enabled: bool | None = None


class MonitorSourceResponse(BaseModel):
    id: int
    path: str
    label: str
    enabled: bool
    created_at: str | None = None
