from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise import Tortoise
from loguru import logger
from pathlib import Path

class RepostTask(models.Model):
    """转发任务模型"""

    id = fields.IntField(pk=True)
    weibo_mid = fields.CharField(max_length=50, description="微博ID")
    content = fields.TextField(description="转发内容")
    created_at = fields.FloatField(description="创建时间戳")
    status = fields.CharField(max_length=20, default="pending", description="任务状态")

    class Meta:
        table = "repost_tasks"
        table_description = "转发任务表"

    def __str__(self):
        return f"RepostTask(id={self.id}, weibo_mid={self.weibo_mid}, status={self.status})"

# 创建Pydantic模型用于序列化
RepostTask_Pydantic = pydantic_model_creator(RepostTask, name="RepostTask")


async def init_database(db_path: Path):
    """初始化Tortoise ORM数据库"""
    await Tortoise.init(
        db_url=f"sqlite://{db_path}", modules={"models": ["src.models"]}
    )
    await Tortoise.generate_schemas()
    logger.info("数据库初始化成功")