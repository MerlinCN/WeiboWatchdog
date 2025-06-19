from pydantic import BaseModel, Field
from typing import Literal


class Setting(BaseModel):
    mode: Literal["dev", "prod"] = Field(default="dev", description="运行模式")
    bypy_token: str = Field(..., description="百度云token")
    tencent_api_key: str = Field(..., description="腾讯云api key")
    tencent_secret_key: str = Field(..., description="腾讯云secret key")
    special_users: list[int] = Field(default_factory=list, description="微博特殊用户")
    repost_interval: int = Field(default=60, description="转发间隔（秒）")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


setting = Setting()
