from tortoise import fields

from .base import BaseModel, TimestampMixin


class Script(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=128, unique=True, index=True, description="脚本名称")
    desc = fields.CharField(max_length=255, null=True, description="描述")
    code = fields.TextField(description="Python 脚本源码")
    requirements = fields.TextField(null=True, description="脚本特定依赖（可选），换行分隔")
    enabled = fields.BooleanField(default=True, description="是否启用", index=True)

    class Meta:
        table = "CrawlerScript"


class ScriptRun(BaseModel, TimestampMixin):
    script: fields.ForeignKeyRelation[Script] = fields.ForeignKeyField(
        "models.Script", related_name="runs", on_delete=fields.CASCADE
    )
    status = fields.CharField(max_length=16, index=True, description="queued|running|success|error|timeout")
    started_at = fields.DatetimeField(null=True, index=True)
    ended_at = fields.DatetimeField(null=True, index=True)
    exit_code = fields.IntField(null=True)
    pid = fields.IntField(null=True, description="子进程PID")
    stdout = fields.TextField(null=True)
    stderr = fields.TextField(null=True)
    duration_ms = fields.IntField(null=True)

    class Meta:
        table = "CrawlerScriptRun"
        indexes = (("script_id", "status"),)


class CrawlerSetting(BaseModel, TimestampMixin):
    id = fields.IntField(pk=True)
    retention_days = fields.IntField(default=30, description="运行日志保留天数")
    default_timeout_sec = fields.IntField(default=600, description="默认超时秒")
    max_log_bytes = fields.IntField(default=1048576, description="单次运行日志最大字节-截断")

    class Meta:
        table = "CrawlerSetting"
