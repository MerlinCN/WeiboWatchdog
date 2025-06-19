from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Literal


class Setting(BaseSettings):
    mode: Literal["dev", "prod"] = Field(default="dev", description="运行模式")
    bypy_config_dir: str = Field(default="config", description="百度云配置目录")
    tencent_api_key: str = Field(default="", description="腾讯云api key")
    tencent_secret_key: str = Field(default="", description="腾讯云secret key")
    special_users: list[int] = Field(default=[], description="微博特殊用户")
    repost_interval: int = Field(default=60, description="转发间隔（秒）")
    bypy_url: str = Field(default="http://localhost:8000", description="百度云上传地址")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


setting = Setting()
