import time
import traceback

from Engine import SpiderEngine
from Util import raiseACall, readSpecialUsers

if __name__ == '__main__':
    wd = SpiderEngine(loggerName="MainLoop")
    raiseACall("启动成功")
    while 1:
        try:
            wd.refreshPage()
            iStartTime = time.time()
            iterDict = {**wd.thisRecommendPagePost, **wd.thisPagePost}
            for _oPost in iterDict.values():
                if wd.isInHistory(_oPost.uid):
                    continue
                if _oPost.video and _oPost.isRecommend is False:  # 现在只点赞视频
                    wd.startRepost(_oPost)  # 现在只点赞视频
                elif wd.specialTopics(_oPost):
                    wd.startRepost(_oPost)
                elif wd.detection(_oPost):  # 检测到图片中有人且大小满足
                    wd.startRepost(_oPost)
                elif not _oPost.isOriginPost():  # 如果不是原创微博
                    lSp = readSpecialUsers()  # 只转发别人微博的博主
                    if _oPost.userUid in lSp:
                        if wd.detection(_oPost.originPost) or _oPost.originPost.video:
                            wd.startRepost(_oPost.originPost)
            iGap = time.time() - iStartTime
            if iGap <= 60:
                interval = 60 - iGap
            else:
                interval = 0
            wd.logger.info("Heartbeat")
            time.sleep(interval)
        except Exception as e:
            wd.logger.error(traceback.format_exc())
            raiseACall(e)
