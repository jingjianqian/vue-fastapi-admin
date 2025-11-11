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
