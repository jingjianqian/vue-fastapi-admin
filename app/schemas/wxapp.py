from pydantic import BaseModel, Field
from typing import Optional, Any


class MpLogin(BaseModel):
    code: str = Field(..., description="wx.login 返回的 code")
    appid: Optional[str] = Field(default=None, description="小程序appid，可选，未传则使用服务端默认配置")
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
