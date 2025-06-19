from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator


class RepostTask(models.Model):
    """转发任务模型"""

    id = fields.IntField(pk=True)
    weibo_mid = fields.CharField(max_length=50, description="微博ID")
    content = fields.TextField(description="转发内容")
    created_at = fields.FloatField(description="创建时间戳")
    retry_count = fields.IntField(default=0, description="重试次数")
    max_retries = fields.IntField(default=3, description="最大重试次数")
    status = fields.CharField(max_length=20, default="pending", description="任务状态")

    class Meta:
        table = "repost_tasks"
        table_description = "转发任务表"

    def __str__(self):
        return f"RepostTask(id={self.id}, weibo_mid={self.weibo_mid}, status={self.status})"


class RepostHistory(models.Model):
    """转发历史模型"""

    id = fields.IntField(pk=True)
    weibo_mid = fields.CharField(max_length=50, description="微博ID")
    content = fields.TextField(description="转发内容")
    created_at = fields.FloatField(description="创建时间戳")
    executed_at = fields.FloatField(description="执行时间戳")
    status = fields.CharField(max_length=20, description="执行状态")

    class Meta:
        table = "repost_history"
        table_description = "转发历史表"

    def __str__(self):
        return f"RepostHistory(id={self.id}, weibo_mid={self.weibo_mid}, status={self.status})"


# 创建Pydantic模型用于序列化
RepostTask_Pydantic = pydantic_model_creator(RepostTask, name="RepostTask")
