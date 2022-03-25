import sys

from Engine import SpiderEngine
from Util import readCookies, is_debug

if is_debug():
    sys.path.append(r"F:\Coding\Python\WeiboBot")

from WeiboBot import Bot
from WeiboBot.weibo import Weibo

myBot = Bot(cookies=readCookies())
wd = SpiderEngine(loggerName="MainLoop")


@myBot.onNewWeibo
async def onNewWeibo(weibo: Weibo):
    is_repost = await wd.is_repost(weibo)
    if is_repost is False:
        return
    is_large_image = await wd.dump_post(weibo)
    if not is_large_image:
        return
    comment = wd.randomComment(weibo)
    is_dual = len(weibo.image_list()) > 6
    
    await myBot.like(weibo.id)
    await myBot.repost_action(weibo.id, content=comment, dualPost=is_dual)
    wd.logger.info(f"结束处理微博 {weibo.detail_url()}")


if __name__ == '__main__':
    myBot.run()
