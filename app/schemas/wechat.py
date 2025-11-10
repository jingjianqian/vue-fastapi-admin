from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field


class PublishStatus(StrEnum):
    DRAFT = "draft"        # 草稿
    REVIEW = "review"      # 审核中
    PUBLISHED = "published"  # 已发布
    DISABLED = "disabled"  # 已下线/禁用


class BaseWechat(BaseModel):
    id: int
    name: str
    appid: str
    secret: str | None = None
    logo_url: Optional[str] = None
    qrcode_url: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    publish_status: PublishStatus = PublishStatus.DRAFT


class WechatCreate(BaseModel):
    name: str = Field(example="我的小程序")
    appid: str = Field(example="wx1234567890abcdef")
    secret: str = Field(example="your_app_secret")
    logo_url: Optional[str] = Field(default=None, example="https://example.com/logo.png")
    qrcode_url: Optional[str] = Field(default=None, example="https://example.com/qrcode.png")
    description: Optional[str] = Field(default=None, example="描述信息")
    version: Optional[str] = Field(default=None, example="1.0.0")
    publish_status: PublishStatus = Field(default=PublishStatus.DRAFT)

    def create_dict(self):
        return self.model_dump(exclude_unset=True)


class WechatUpdate(BaseModel):
    id: int
    name: Optional[str] = None
    appid: Optional[str] = None
    secret: Optional[str] = None
    logo_url: Optional[str] = None
    qrcode_url: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    publish_status: Optional[PublishStatus] = None


class WechatUpdateLogo(BaseModel):
    id: int
    logo_url: str


class WechatUpdateQrcode(BaseModel):
    id: int
    qrcode_url: str


class WechatUpdateStatus(BaseModel):
    id: int
    publish_status: PublishStatus