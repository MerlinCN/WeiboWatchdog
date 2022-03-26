import asyncio

from WeiboBot import Bot
from engine import SpiderEngine
from util import read_cookies

myBot = Bot(cookies=read_cookies())
wd = SpiderEngine(loggerName="Test")


async def is_repost(weibo_id):
    weibo = await myBot.get_weibo(weibo_id)
    result = await wd.is_repost(weibo)
    result_str = "可转发" if result else "不可转发"
    wd.logger.info(result_str)


async def main():
    await asyncio.wait_for(myBot.login(), timeout=10)


if __name__ == '__main__':
    asyncio.run(main())
