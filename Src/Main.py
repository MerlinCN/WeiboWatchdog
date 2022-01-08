import random
import time
import traceback

from Engine import SpiderEngine
from Util import raiseACall, readSpecialUsers

if __name__ == '__main__':
    wd = SpiderEngine(loggerName="MainLoop")
    raiseACall("启动成功")
    while 1:
        try:
            # 下面是时间限制，但微博对刷新没有做啥限制，所以多刷新也没啥，没必要开
            # if 2 <= datetime.now().hour < 6:
            #     wd.logger.info("Heartbeat without request")
            #     time.sleep(60)
            #     continue
            wd.refreshPage()
            # 下面是寻找热门推荐，不建议开，微博的算法容易推荐奇怪的东西
            # time.sleep(5)
            # wd.refreshRecommend()
            iStartTime = time.time()
            iterDict = {**wd.thisRecommendPagePost, **wd.thisPagePost}
            for _oPost in iterDict.values():
                if wd.isInHistory(_oPost.uid):
                    continue
                if _oPost.video and _oPost.isRecommend is False:  # 转发视频（但热门推荐除外）
                    wd.startRepost(_oPost)
                elif wd.detection(_oPost):
                    wd.startRepost(_oPost)
                elif not _oPost.isOriginPost():
                    lSp = readSpecialUsers()  # 只转发别人微博的博主
                    if _oPost.userUid in lSp:
                        if wd.detection(_oPost.originPost) or _oPost.originPost.video:
                            wd.startRepost(_oPost.originPost)
            if time.time() - iStartTime <= 60 * 1000:
                interval = random.randint(50, 60)
            else:
                interval = 5
            wd.logger.info("Heartbeat")
            time.sleep(interval)
        except Exception as e:
            wd.logger.error(traceback.format_exc())
            raiseACall(e)
