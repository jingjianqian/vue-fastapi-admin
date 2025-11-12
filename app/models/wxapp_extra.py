from tortoise import fields

from app.models.base import BaseModel, TimestampMixin


class Category(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=64, unique=True)
    icon_url = fields.CharField(max_length=255, null=True)
    sort = fields.IntField(default=0)
    is_online = fields.BooleanField(default=True)

    class Meta:
        table = "Category"


class Banner(BaseModel, TimestampMixin):
    image_url = fields.CharField(max_length=255)
    title = fields.CharField(max_length=64, null=True)
    # 软外键：后续可替换为 ForeignKeyField("models.WechatApp")
    app_id = fields.IntField(null=True)
    jump_appid = fields.CharField(max_length=64, null=True)
    jump_path = fields.CharField(max_length=128, null=True)
    sort = fields.IntField(default=0)
    is_online = fields.BooleanField(default=True)

    class Meta:
        table = "Banner"


class Favorite(BaseModel, TimestampMixin):
    user_id = fields.IntField()
    app_id = fields.IntField()
    is_pinned = fields.BooleanField(default=False)

    class Meta:
        table = "Favorite"
        unique_together = ("user_id", "app_id")


class Event(BaseModel, TimestampMixin):
    user_id = fields.IntField(null=True)
    event = fields.CharField(max_length=64)
    payload = fields.JSONField(null=True)

    class Meta:
        table = "Event"


class WxUser(BaseModel, TimestampMixin):
    """微信用户表（独立于系统用户表）"""
    wx_openid = fields.CharField(max_length=64, unique=True, index=True, description="微信OpenID")
    wx_unionid = fields.CharField(max_length=64, null=True, index=True, description="微信UnionID")
    nickname = fields.CharField(max_length=64, null=True, description="昵称")
    avatar_url = fields.CharField(max_length=255, null=True, description="头像URL")
    phone = fields.CharField(max_length=20, null=True, description="手机号")
    is_active = fields.BooleanField(default=True, description="是否激活", index=True)
    last_login_at = fields.DatetimeField(null=True, description="最后登录时间")
    
    class Meta:
        table = "WxUser"
