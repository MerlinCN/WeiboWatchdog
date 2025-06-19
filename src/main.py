import random
import asyncio
from pathlib import Path

from WeiboBot import Bot
from WeiboBot.model import Weibo, Comment
from engine import SpiderEngine
from const import COMMENTS
from loguru import logger
from ai import dectection
from config import setting
import httpx

bot = Bot(cookies=Path("data")/ "weibobot_cookies.json",db_path=Path("data")/"weibo_bot.db")
wd = SpiderEngine(bot, repost_interval=setting.repost_interval)


def select_comment(weibo: Weibo):
    if len(weibo.image_list()) < 6:
        return "转发微博"

    comment = random.choice(COMMENTS) * random.randint(1, 3)
    return comment


async def upload_file(file_path: Path, remote_path: Path):
    async with httpx.AsyncClient() as client:
        url = setting.bypy_url + "/upload"
        params = {"path": str(file_path), "remote_path": str(remote_path)}
        response = await client.get(url, params=params)
        response.raise_for_status()
        logger.info(f"上传文件 {file_path}")


@bot.onMentionCmt
async def on_mention_cmt(cmt: Comment):
    try:
        logger.info(
            f"开始处理@{cmt.user.screen_name} 请求转发微博 {cmt.root_weibo.detail_url()}"
        )
        root_weibo = cmt.root_weibo.retweeted_status or cmt.root_weibo
        if bot.is_weibo_repost(root_weibo.mid) is True:
            logger.info(f"已经转发过微博 {root_weibo.detail_url()}")
            return
        weibo = root_weibo
        await wd.dump_post(weibo)
        comment = select_comment(weibo)
        await wd.add_repost_task(weibo.mid, comment)
        logger.info(f"结束处理微博 {weibo.detail_url()}")
    except Exception as e:
        logger.error(f"处理@我的评论出错: {e},metadata:\n{cmt.metadata}\n")


@bot.onNewWeibo
async def on_new_weibo(_weibo: Weibo):
    try:
        logger.info(f"开始处理微博 {_weibo.detail_url()}")
        weibo = await wd.pre_detection(_weibo)
        if not weibo:
            return

        if bot.is_weibo_repost(weibo.mid) is True:
            logger.info(f"已经转发过微博 {weibo.detail_url()}")
            return
        result = await dectection(weibo)
        file_path = (
            Path("cache") / f"{weibo.user.mid}_{weibo.user.screen_name}" / weibo.mid
        )
        if not result:
            logger.info(f"微博 {weibo.detail_url()} 未检测到内容")
            await wd.clean_cache(file_path)
            return
        remote_path = (
            Path("wbd") / f"{weibo.user.mid}_{weibo.user.screen_name}" / weibo.mid
        )
        await upload_file(file_path, remote_path)
        comment = select_comment(weibo)
        await wd.add_repost_task(weibo.mid, comment)
        logger.info(f"结束处理微博 {weibo.detail_url()}")
    except Exception as e:
        logger.error(
            f"处理微博 {_weibo.detail_url()} 出错: {e},metadata:\n{_weibo.metadata}\n"
        )


if __name__ == "__main__":
    try:
        wd.run()
    except KeyboardInterrupt:
        logger.info("正在关闭程序...")
        asyncio.run(wd.close())
