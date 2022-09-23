from WeiboBot import Bot
from WeiboBot.message import Message

cmd_func = {

}


def command(cmd):
    def decorate(func):
        cmd_func[cmd] = func

    return decorate


@command("/help")
async def bot_help(bot: Bot, msg: Message, *args):
    await bot.send_message(msg.sender_id, content="这是一条帮助")


@command("/repost")
async def repost(bot: Bot, msg: Message, *args):
    """
    转发微博

    :param bot:
    :param msg:
    :param args:微博id
    :return:
    """
    mid = int(args[0])
    weibo = await bot.get_weibo(mid)
    if weibo is None:
        await bot.send_message(msg.sender_id, "找不到该微博")
    else:
        new_weibo = await bot.repost_weibo(mid)
        await bot.send_message(msg.sender_id, f"转发微博成功 {new_weibo.detail_url()}")


@command("/del")
async def del_weibo(bot: Bot, msg: Message, *args):
    mid = int(args[0])
    weibo = await bot.get_weibo(mid)
    if weibo is None:
        await bot.send_message(msg.sender_id, "找不到该微博")
    else:
        ok = await bot.del_weibo(mid)
        if ok == 1:
            await bot.send_message(msg.sender_id, f"删除微博成功 {weibo.detail_url()}")
        else:
            await bot.send_message(msg.sender_id, f"删除微博失败 {weibo.detail_url()}")
