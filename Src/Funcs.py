import sys
import traceback

from Engine import SpiderEngine
from Post import CPost


class SubFunctions(SpiderEngine):
    def __init__(self):
        super(SubFunctions, self).__init__(loggerName="SubFuncs")
    
    def selectFunc(self, funcName: str, *args):
        self.logger.info(f"收到命令【{funcName}】,参数为:{args}")
        if funcName == "repost":
            oPost = self.parseOnePost(args[0])
            self.startRepost(oPost)
        elif funcName == "dump":
            oPost = self.parseOnePost(args[0])
            self.dump_post(oPost, canDuplicable=True)
        elif funcName == "isInHistory":
            oPost = self.parseOnePost(args[0])
            result = self.isInHistory(oPost.uid)
            if result is True:
                self.logger.info(f"存在已转发的微博{oPost.uid}")
            else:
                self.logger.info(f"不存在已转发的微博{oPost.uid}")
        else:
            self.logger.error(f"找不到函数{funcName}")
            return
    
    def repost(self, oPost: CPost, *args, **kwargs) -> bool:
        """
        转发微博

        :param oPost: 微博
        :return: 是否成功
        """
        st, _ = self.get_st()
        url = "https://m.weibo.cn/api/statuses/repost"
        content = "转发微博"
        mid = oPost.uid
        data = {"id": mid, "content": content, "mid": mid, "st": st, "_spr": "screen:2560x1440"}
        self.logger.info(f"开始处理{oPost.userName}（{oPost.userUid}）的微博 {self.postDetail(oPost)}")
        
        self.dump_post(oPost, canDuplicable=True)
        if oPost.onlyFans:
            self.logger.info(f"微博仅粉丝可见，不可转载。")
            self.updateHistory(mid)
            return False
        # 这里一定要加referer， 不加会变成不合法的请求
        self.add_ref(f"https://m.weibo.cn/compose/repost?id={mid}")
        self.header["x-xsrf-token"] = st
        r = self.mainSession.post(url, data=data, headers=self.header)
        if r.status_code != 200:  # 转发过多后
            self.logger.error("请求错误")
            return False
        try:
            if r.json().get("ok") == 1:
                self.logger.info(f'转发微博成功')
                self.updateHistory(mid)
                self.like(oPost)
                return True
            else:
                err = r.json()
                self.logger.error(
                    f'转发微博失败 \n {err["msg"]} \n {r.json()}')
                return False
        
        except Exception as e:
            self.logger.error(r.text)
            self.logger.error(e)
            return False


if __name__ == '__main__':
    sf = SubFunctions()
    try:
        sf.selectFunc(*sys.argv[1:])
    except Exception as e:
        sf.logger.error(traceback.format_exc())