from Engine import SpiderEngine
from Util import readCookies

from WeiboBot import Bot
from WeiboBot.weibo import Weibo

myBot = Bot(cookies=readCookies())
wd = SpiderEngine(loggerName="MainLoop")


@myBot.onNewWeibo
async def onNewWeibo(weibo: Weibo):
    if wd.is_had_scan(weibo) is True:
        return False
    is_repost = await wd.is_repost(weibo)
    if is_repost is False:
        return
    wd.logger.info(f"开始处理微博 {weibo.detail_url()}")
    is_large_image = await wd.dump_post(weibo)
    if not is_large_image:
        wd.logger.info(f"图片/视频太小,不转载")
        wd.logger.info(f"结束处理微博 {weibo.detail_url()}")
        return
    comment = wd.randomComment(weibo)
    is_dual = len(weibo.image_list()) > 6

    await myBot.like_weibo(weibo.id)
    myBot.repost_action(weibo.id, content=comment, dualPost=is_dual)
    wd.logger.info(f"结束处理微博 {weibo.detail_url()}")


if __name__ == '__main__':
    myBot.run()
