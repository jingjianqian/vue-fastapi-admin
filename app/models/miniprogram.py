from tortoise import fields

from app.models.base import BaseModel, TimestampMixin


class Miniprogram(BaseModel, TimestampMixin):
    """小程序主表"""
    # 基本信息
    source_id = fields.BigIntField(unique=True, index=True, description="来源平台的ID（如we123的ID）")
    name = fields.CharField(max_length=255, description="小程序名称", index=True)
    category = fields.CharField(max_length=100, null=True, description="分类")
    
    # 描述信息
    description = fields.TextField(null=True, description="小程序介绍")
    update_time_text = fields.CharField(max_length=50, null=True, description="更新时间（原始文本）")
    view_count = fields.CharField(max_length=50, null=True, description="查看次数")
    
    # 图片信息
    logo_url = fields.TextField(null=True, description="Logo URL")
    logo_local_path = fields.CharField(max_length=500, null=True, description="Logo本地路径")
    qrcode_url = fields.TextField(null=True, description="详情页二维码图片URL")
    
    # 来源信息
    source_url = fields.TextField(null=True, description="来源页面URL")
    source_platform = fields.CharField(max_length=50, default="we123", description="来源平台")
    crawl_time = fields.DatetimeField(null=True, description="爬取时间")
    
    # 关联关系（反向引用）
    # tags: ReverseRelation["MiniprogramTag"]
    # screenshots: ReverseRelation["MiniprogramScreenshot"]
    # related_links: ReverseRelation["MiniprogramRelatedLink"]
    
    class Meta:
        table = "miniprogram"
        indexes = [("source_platform", "source_id")]


class MiniprogramTag(BaseModel, TimestampMixin):
    """小程序标签表"""
    miniprogram = fields.ForeignKeyField(
        "models.Miniprogram",
        related_name="tags",
        on_delete=fields.CASCADE,
        description="关联的小程序"
    )
    tag_name = fields.CharField(max_length=100, description="标签名称", index=True)
    
    class Meta:
        table = "miniprogram_tag"
        unique_together = (("miniprogram", "tag_name"),)


class MiniprogramScreenshot(BaseModel, TimestampMixin):
    """小程序截图表"""
    miniprogram = fields.ForeignKeyField(
        "models.Miniprogram",
        related_name="screenshots",
        on_delete=fields.CASCADE,
        description="关联的小程序"
    )
    image_url = fields.TextField(description="截图URL")
    image_local_path = fields.CharField(max_length=500, null=True, description="截图本地路径")
    image_order = fields.IntField(default=0, description="截图顺序")
    
    class Meta:
        table = "miniprogram_screenshot"
        ordering = ["image_order"]


class MiniprogramRelatedLink(BaseModel, TimestampMixin):
    """小程序关联链接表"""
    miniprogram = fields.ForeignKeyField(
        "models.Miniprogram",
        related_name="related_links",
        on_delete=fields.CASCADE,
        description="关联的小程序"
    )
    link_url = fields.TextField(description="关联链接URL")
    link_order = fields.IntField(default=0, description="链接顺序")
    
    class Meta:
        table = "miniprogram_related_link"
        ordering = ["link_order"]
