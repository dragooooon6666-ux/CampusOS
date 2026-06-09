"""组织管理 — Pydantic 模型"""

from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    icon: str = "📋"
    sort_order: int = 0


class OrganizationUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    icon: str | None = None
    sort_order: int | None = None


class OrganizationResponse(BaseModel):
    id: int
    name: str
    icon: str
    sort_order: int
    created_at: str | None = None


class FolderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    sort_order: int = 0


class FolderUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    sort_order: int | None = None


class FolderResponse(BaseModel):
    id: int
    organization_id: int
    name: str
    sort_order: int
    created_at: str | None = None
