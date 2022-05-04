import asyncio

from main import *


async def is_repost(weibo_id):
    weibo = await myBot.get_weibo(weibo_id)
    result = await wd.is_process(weibo)
    result_str = "可转发" if result else "不可转发"
    wd.logger.info(result_str)


async def main():
    await asyncio.wait_for(myBot.login(), timeout=10)


if __name__ == '__main__':
    asyncio.run(main())
