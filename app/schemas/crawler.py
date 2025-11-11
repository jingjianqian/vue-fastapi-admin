from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional


class CreateTaskIn(BaseModel):
    name: str = Field(..., description="任务名称")
    source: str = Field(..., description="数据源 we123_miniprogram")
    start_id: Optional[int] = Field(default=1, ge=1)
    is_loop: Optional[bool] = Field(default=False)
    max_consecutive_404: Optional[int] = Field(default=500, ge=1, le=10000)
    concurrency: Optional[int] = Field(default=1, ge=1, le=8)
    delay_ms: Optional[int] = Field(default=0, ge=0, le=60000)
    max_retries: Optional[int] = Field(default=1, ge=1, le=5)
    proxy: Optional[str] = Field(default=None, description="http(s)://host:port")


class StartStopIn(BaseModel):
    id: int


class TaskUpdateIn(BaseModel):
    id: int
    is_loop: Optional[bool] = None
    max_consecutive_404: Optional[int] = Field(default=None, ge=1, le=10000)
    concurrency: Optional[int] = Field(default=None, ge=1, le=8)
    delay_ms: Optional[int] = Field(default=None, ge=0, le=60000)
    max_retries: Optional[int] = Field(default=None, ge=1, le=5)
    proxy: Optional[str] = None


class SyncOdsIn(BaseModel):
    only_new: bool = Field(default=True, description="仅创建新记录（存在则跳过）")
    overwrite: bool = Field(default=False, description="覆盖已存在的字段")
    include_no_appid: bool = Field(default=False, description="是否导入无 appid 的记录（默认跳过）")
    limit: Optional[int] = Field(default=500, ge=1, le=5000)
