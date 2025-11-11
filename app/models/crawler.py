from tortoise import fields

from .base import BaseModel, TimestampMixin


class CrawlerTask(BaseModel, TimestampMixin):
    """爬虫任务配置与运行状态
    - source: 爬虫来源标识，如 we123_miniprogram
    - start_id: 起始 ID（默认 1）
    - next_id: 下一个待爬取的 ID（断点续爬）
    - max_consecutive_404: 连续 404 达到阈值视为爬取完毕
    - is_loop: 是否循环（达到阈值后从 1 重新开始）
    - status: idle|running|stopped|finished|error
    - concurrency: 并发抓取数
    - delay_ms: 批次间隔（毫秒）
    - max_retries: 单条抓取失败重试次数（不含 404）
    - proxy: 代理设置（如 http://host:port）
    """

    name = fields.CharField(max_length=64, description="任务名称", index=True)
    source = fields.CharField(max_length=32, description="数据源标识", index=True)

    start_id = fields.IntField(default=1, description="起始 ID")
    next_id = fields.IntField(default=1, description="下一次爬取的 ID")

    max_consecutive_404 = fields.IntField(default=500, description="连续 404 阈值")
    consecutive_404 = fields.IntField(default=0, description="当前连续 404 计数")

    is_loop = fields.BooleanField(default=False, description="是否循环")

    # 新增运行参数
    concurrency = fields.IntField(default=1, description="并发数", index=True)
    delay_ms = fields.IntField(default=0, description="批间延迟ms")
    max_retries = fields.IntField(default=1, description="失败重试次数")
    proxy = fields.CharField(max_length=255, null=True, description="代理")

    status = fields.CharField(max_length=16, default="idle", description="运行状态", index=True)
    last_error = fields.TextField(null=True, description="最后一次错误")
    last_run_at = fields.DatetimeField(null=True, description="最后运行时间", index=True)
    created_by = fields.IntField(null=True, description="创建人（用户ID）", index=True)

    class Meta:
        table = "CrawlerTask"
        indexes = (("source", "status"),)


class OdsWe123MiniProgram(BaseModel, TimestampMixin):
    """ODS-微信小程序（we123.com）原始数据存储
    兼容 doc/wechat.md 中小程序管理的核心字段（可为空），并保留 raw_html/raw_data 便于后处理
    """

    we123_id = fields.IntField(unique=True, description="we123 站内ID", index=True)

    # 兼容管理字段（可为空）
    name = fields.CharField(max_length=128, null=True, description="名称", index=True)
    appid = fields.CharField(max_length=64, null=True, description="AppID", index=True)
    logo_url = fields.CharField(max_length=512, null=True, description="图标URL")
    qrcode_url = fields.CharField(max_length=512, null=True, description="二维码URL")
    description = fields.TextField(null=True, description="描述")
    category = fields.CharField(max_length=128, null=True, description="分类")
    developer = fields.CharField(max_length=128, null=True, description="开发者/主体")

    # 原始内容
    raw_html = fields.TextField(null=True, description="页面HTML")
    raw_data = fields.JSONField(null=True, description="解析出的原始数据")

    # 抓取状态
    fetch_status = fields.CharField(max_length=16, default="ok", description="ok|404|error", index=True)
    fetch_error = fields.TextField(null=True, description="错误详情")

    class Meta:
        table = "ODS_We123MiniProgram"