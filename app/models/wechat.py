from tortoise import fields

from app.models.base import BaseModel, TimestampMixin
from app.schemas.wechat import PublishStatus


class WechatApp(BaseModel, TimestampMixin):
    """小程序信息表

    注：为兼容现有库中的表结构，表名沿用 `MyWechat`（如需变更，请同步更新迁移和数据复制脚本）。
    不包含部门字段，适用于个人项目。
    """

    name = fields.CharField(max_length=64, description="小程序名称", index=True)
    appid = fields.CharField(max_length=64, unique=True, description="AppID", index=True)
    secret = fields.CharField(max_length=128, description="AppSecret")
    logo_url = fields.CharField(max_length=255, null=True, description="小程序图标URL")
    qrcode_url = fields.CharField(max_length=255, null=True, description="二维码URL")
    description = fields.TextField(null=True, description="描述")
    version = fields.CharField(max_length=32, null=True, description="版本号", index=True)
    publish_status = fields.CharEnumField(PublishStatus, default=PublishStatus.DRAFT, description="发布状态", index=True)
    is_deleted = fields.BooleanField(default=False, description="是否删除标记", index=True)
    
    # 小程序端展示字段
    category_id = fields.IntField(null=True, description="分类ID")
    is_top = fields.BooleanField(default=False, description="后台置顶")
    jump_path = fields.CharField(max_length=128, null=True, description="可选直跳路径")

    class Meta:
        table = "MyWechat"
