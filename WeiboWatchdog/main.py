import random

from WeiboBot import Bot
from WeiboBot.comment import Comment
from WeiboBot.weibo import Weibo

import config
from const import *
from engine import SpiderEngine
from util import bark_call

myBot = Bot(cookies=config.cookies)
wd = SpiderEngine(loggerName="MainLoop")


def select_comment(weibo: Weibo):
    if len(weibo.image_list()) < 6:
        return "转发微博"

    comment = random.choice(COMMENTS) * random.randint(1, 3)
    return comment


@myBot.onMentionCmt
async def on_mention_cmt(cmt: Comment):
    try:
        root_weibo = cmt.root_weibo.original_weibo if cmt.root_weibo.original_weibo else cmt.root_weibo
        if myBot.is_weibo_repost(root_weibo.weibo_id()) is True:
            wd.logger.info(f"已经转发过微博 {root_weibo.detail_url()}")
            return
        weibo = root_weibo
        wd.logger.info(f"开始处理@{cmt.user['screen_name']} 请求转发微博 {weibo.detail_url()}")
        await wd.dump_post(weibo)
        comment = select_comment(weibo)
        if config.is_repost is True:
            myBot.repost_action(weibo.weibo_id(), content=comment)
        wd.logger.info(f"结束处理微博 {weibo.detail_url()}")
    except Exception as e:
        wd.logger.error(f"处理@我的评论出错: {e}")
        bark_call(f"处理@我的评论出错")


@myBot.onNewWeibo
async def on_new_weibo(weibo: Weibo):
    try:
        is_process = await wd.is_process(weibo)
        if is_process is False:
            return
        if weibo.original_weibo is not None:
            target_weibo = weibo.original_weibo
        else:
            target_weibo = weibo
        if myBot.is_weibo_repost(target_weibo.weibo_id()) is True:
            wd.logger.info(f"已经处理过微博 {target_weibo.detail_url()}")
            return
        wd.logger.info(f"开始处理微博 {target_weibo.detail_url()}")
        is_large_image = await wd.dump_post(target_weibo)
        if not is_large_image:
            wd.logger.info(f"图片/视频太小")
            wd.logger.info(f"结束处理微博 {target_weibo.detail_url()}")
            return

        comment = select_comment(target_weibo)
        is_dual = len(target_weibo.image_list()) > 6
        if config.is_repost is True:
            myBot.repost_action(target_weibo.weibo_id(), content=comment, dualPost=is_dual)
        # await myBot.like_weibo(target_weibo.weibo_id())
        wd.logger.info(f"结束处理微博 {weibo.detail_url()}")
    except Exception as e:
        wd.logger.error(f"处理微博 {weibo.detail_url()} 出错: {e}")
        bark_call(f"处理微博出错", weibo.scheme)


if __name__ == '__main__':
    myBot.run()
