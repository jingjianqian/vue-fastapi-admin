from pydantic import BaseModel, Field
from typing import Optional, Any


class MpLogin(BaseModel):
    code: str = Field(..., description="wx.login 返回的 code")
    nickname: Optional[str] = Field(default=None)
    avatarUrl: Optional[str] = Field(default=None)


class FavoriteToggle(BaseModel):
    app_id: int
    value: bool = Field(..., description="True=收藏, False=取消")


class FavoritePin(BaseModel):
    app_id: int
    value: bool = Field(..., description="True=设为常用, False=取消")


class TrackEvent(BaseModel):
    event: str
    payload: Optional[dict[str, Any]] = None
