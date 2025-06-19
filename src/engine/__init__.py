from WeiboBot import Bot
from WeiboBot.model import Weibo
from loguru import logger
from pathlib import Path
import httpx
from config import setting
import shutil
import time
import asyncio
from typing import List
from dataclasses import dataclass
from tortoise import Tortoise
from models import RepostTask, init_database
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


@dataclass
class RepostTaskData:
    """转发任务数据结构（内存中）"""

    weibo_mid: str
    content: str
    created_at: float


class SpiderEngine:
    def __init__(self, bot: Bot, repost_interval: int = 60):
        self.bot = bot
        self.repost_interval = repost_interval  # 转发间隔（秒）
        self.last_repost_time = 0  # 上次转发时间
        self.repost_queue: List[RepostTaskData] = []
        self.db_path = self.bot.db_path



    async def _load_queue(self):
        """从数据库加载转发队列"""
        try:
            # 查询待处理的任务
            tasks = await RepostTask.filter(status="pending").order_by("created_at")

            self.repost_queue = [
                RepostTaskData(
                    weibo_mid=task.weibo_mid,
                    content=task.content,
                    created_at=task.created_at,
                )
                for task in tasks
            ]

            logger.info(f"从数据库加载了 {len(self.repost_queue)} 个转发任务")
        except Exception as e:
            logger.error(f"加载转发队列失败: {e}")
            self.repost_queue = []

    async def _save_queue(self):
        """保存转发队列到数据库"""
        try:
            # 清空待处理任务
            await RepostTask.filter(status="pending").delete()

            # 重新插入当前队列中的任务
            for task_data in self.repost_queue:
                await RepostTask.create(
                    weibo_mid=task_data.weibo_mid,
                    content=task_data.content,
                    created_at=task_data.created_at,
                    status="pending",
                )
        except Exception as e:
            logger.error(f"保存转发队列失败: {e}")

        

    async def _repost_worker(self):
        """转发工作线程，处理队列中的转发任务"""
        # 初始化数据库
        await init_database(self.db_path)
        await self._load_queue()

        while True:
            try:
                if self.repost_queue:
                    current_time = time.time()
                    # 检查是否达到转发间隔
                    if current_time - self.last_repost_time >= self.repost_interval:
                        task = self.repost_queue.pop(0)
                        await self._execute_repost(task)
                        self.last_repost_time = current_time
                        await self._save_queue()  # 保存更新后的队列
                        logger.info(f"执行转发任务: {task.weibo_mid}")
                    else:
                        # 等待一段时间再检查
                        await asyncio.sleep(1)
                else:
                    # 队列为空，等待更长时间
                    await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"转发工作线程出错: {e}")
                await asyncio.sleep(5)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception),
        before_sleep=lambda retry_state: logger.warning(
            f"转发微博失败，第 {retry_state.attempt_number} 次重试: {retry_state.outcome.exception()}"
        ),
    )
    async def _execute_repost(self, task: RepostTaskData):
        """执行转发任务"""
        try:
            if setting.mode == "prod":
                await self.bot.repost_weibo(task.weibo_mid, content=task.content)
                logger.info(f"成功转发微博 {task.weibo_mid}")
            else:
                logger.info(f"成功转发微博 {task.weibo_mid}")
        except Exception as e:
            logger.error(f"转发微博 {task.weibo_mid} 失败: {e}")
            raise  # 重新抛出异常，让 tenacity 处理重试

    async def add_repost_task(self, weibo_mid: str, content: str):
        """添加转发任务到队列"""
        task = RepostTaskData(
            weibo_mid=weibo_mid, content=content, created_at=time.time()
        )
        self.repost_queue.append(task)
        await self._save_queue()
        logger.info(f"添加转发任务到队列: {weibo_mid}")

    async def close(self):
        """关闭数据库连接"""
        await Tortoise.close_connections()

    async def _save_file(self, url: str, file_path: Path, description: str) -> bool:
        """保存文件到指定路径"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
            with open(file_path, "wb") as f:
                f.write(response.content)
            logger.info(f"保存{description}成功")
            return True
        except Exception as e:
            logger.error(f"保存{description}失败:{type(e)}:{e}")
            return False

    async def _save_screenshot(self, weibo: Weibo, save_path: Path) -> None:
        """保存微博截图"""
        try:
            screenshot = await self.bot.screenshot_weibo(weibo.detail_url())
            with open(save_path / f"{weibo.mid}.png", "wb") as f:
                f.write(screenshot)
            logger.info(f"{weibo.mid}微博截图成功")
        except Exception as e:
            logger.error(f"{weibo.mid}微博截图失败:{type(e)}:{e}")

    def _save_metadata(self, weibo: Weibo, save_path: Path) -> None:
        """保存微博元数据"""
        with open(save_path / f"{weibo.mid}.txt", "w", encoding="utf8") as f:
            f.write(f"{weibo.user.screen_name}\n")
            f.write(f"{weibo.created_at}\n")
            f.write(weibo.text + "\n")
            for live_photo in weibo.live_photo:
                f.write(live_photo + "\n")
            if weibo.video_url():
                f.write(weibo.video_url())

    async def dump_post(self, weibo: Weibo) -> Path | None:
        # 初始化路径和变量
        save_path = (
            Path("cache") / f"{weibo.user.mid}_{weibo.user.screen_name}" / weibo.mid
        )
        threshold = 1e6 * 0.3  # 图片大小阈值 300kb
        max_image_size = 0
        save_path.mkdir(parents=True, exist_ok=True)

        # 保存截图
        await self._save_screenshot(weibo, save_path)

        # 保存元数据
        self._save_metadata(weibo, save_path)

        # 保存视频
        if weibo.video_url():
            await self._save_file(
                weibo.video_url(), save_path / f"{weibo.mid}.mp4", "微博视频"
            )

        # 保存LivePhotos
        for idx, live_photo in enumerate(weibo.live_photo):
            await self._save_file(
                live_photo,
                save_path / f"{weibo.mid}_{idx + 1}.mov",
                f"微博LivePhotos{idx + 1}",
            )

        # 保存图片并计算最大尺寸
        for idx, image in enumerate(weibo.image_list()):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(image)
                image_path = save_path / Path(image).name
                with open(image_path, "wb") as f:
                    max_image_size = max(max_image_size, len(response.content))
                    f.write(response.content)
                logger.info(f"保存微博图片{idx + 1}成功")
            except Exception as e:
                logger.error(f"{weibo.mid}保存微博图片{idx + 1}失败:{type(e)}:{e}")

        # 记录图片大小信息
        logger.info("保存微博内容成功")
        size_mb = max_image_size / 1e6
        threshold_mb = threshold / 1e6
        if weibo.image_list():
            status = "大于等于" if max_image_size >= threshold else "小于"
            logger.info(f"图片最大size为{size_mb:.2f}mb {status}{threshold_mb:.2f}mb")

        # 判断是否需要保留文件夹
        has_valuable_content = (
            max_image_size >= threshold or weibo.live_photo or weibo.video_url()
        )

        if has_valuable_content:
            return save_path
        else:
            shutil.rmtree(save_path)
            return None

    async def clean_cache(self, path: Path):
        if path.exists():
            shutil.rmtree(path)
        logger.info(f"清除缓存 {path}")

    async def pre_detection(self, weibo: Weibo) -> Weibo | None:
        # 确定要处理的微博对象
        target_weibo = weibo.retweeted_status if weibo.retweeted_status else weibo

        # 如果是转发微博，只处理特殊用户的转发
        if weibo.retweeted_status and weibo.mid not in setting.special_users:
            return None

        # 检查微博是否可见
        if not target_weibo.is_visible():
            logger.info("微博不可见,不继续处理")
            return None

        # 检查是否包含直播链接
        if target_weibo.text.find("房间号") > 0:
            logger.info("微博带直播链接,不继续处理")
            return None

        # 检查是否有媒体内容
        has_media = (
            len(target_weibo.image_list()) > 0
            or target_weibo.live_photo
            or target_weibo.video_url()
        )
        if not has_media:
            logger.info("微博没有图片/视频,不继续处理")
            return None

        # 保存微博内容
        if await self.dump_post(target_weibo):
            return target_weibo

        return None

    def run(self):
        loop = asyncio.get_event_loop()
        try:
            loop.create_task(self._repost_worker())
            loop.run_until_complete(self.bot.lifecycle())
        except KeyboardInterrupt:
            loop.close()
