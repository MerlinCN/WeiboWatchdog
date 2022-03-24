import json
import sys
import time
import traceback
from enum import Enum, unique

from Engine import SpiderEngine
from PCS import uploadFiles
from Post import CPost


@unique
class FuncsType(Enum):
    repost = 0  # 转发
    dump = 1  # 保存
    isInHistory = 2  # 查询历史


class SubFunctions(SpiderEngine):
    def __init__(self):
        super(SubFunctions, self).__init__(loggerName="SubFuncs", printLog=False)
    
    def selectFunc(self, funcName: str, *args):
        self.logger.info(f"收到命令【{funcName}】,参数为:{args}")
        dRes = {"ok": 1, "msg": "命令执行成功"}
        funcType: int = int(funcName)
        if funcType == FuncsType.repost.value:
            oPost = self.parseOnePost(args[0])
            if self.startRepost(oPost) is True:
                dRes["msg"] = f"转发微博成功"
            else:
                dRes["msg"] = f"转发微博失败"
        elif funcType == FuncsType.dump.value:
            oPost = self.parseOnePost(args[0])
            if self.dump_post(oPost, canDuplicable=True) is True:
                dRes["msg"] = f"保存微博成功"
            else:
                dRes["msg"] = f"保存微博失败"
        elif funcType == FuncsType.isInHistory.value:
            oPost = self.parseOnePost(args[0])
            if self.isInHistory(oPost.uid) is True:
                dRes["msg"] = f"存在已转发的微博"
            else:
                dRes["msg"] = f"不存在已转发的微博"
        
        else:
            self.logger.error(f"找不到函数{funcType}")
            dRes["ok"] = 0
            dRes["msg"] = f"找不到函数{funcType}"
        return dRes
    
    def repost(self, oPost: CPost, extra_data=None, *args, **kwargs) -> bool:
        """
        转发微博

        :param oPost: 微博
        :return: 是否成功
        """
        st, _ = self.get_st()
        url = "https://m.weibo.cn/api/statuses/repost"
        content = "转发微博"
        mid = oPost.uid
        if not extra_data:
            data = {"id": mid, "content": content, "mid": mid, "st": st, "_spr": "screen:2560x1440"}
            self.dump_post(oPost, canDuplicable=True)
            self.logger.info(f"开始处理{oPost.userName}({oPost.userUid})的微博 {oPost.Url()}")
        else:
            data = extra_data

        if oPost.onlyFans:
            self.logger.info(f"微博仅粉丝可见，不可转载。")
            self.updateHistory(mid)
            return False
        # 这里一定要加referer， 不加会变成不合法的请求
        self.add_ref(f"https://m.weibo.cn/compose/repost?id={mid}")
        self.header["x-xsrf-token"] = st
        data["content"] = self.randomComment()
        data["dualPost"] = 1
        r = self.mainSession.post(url, data=data, headers=self.header)
        if r.status_code != 200:  # 转发过多后
            self.logger.error("请求错误")
            return False
        try:
            if r.json().get("ok") == 1:
                self.logger.info(f'转发微博成功')
                if not self.isInHistory(oPost.uid):
                    self.updateHistory(mid)
                self.like(oPost)
                return True
            else:
                err = r.json()
                error_type = err["error_type"]
                self.logger.error(
                    f'转发微博失败 \n {err["msg"]} \n {r.json()}')
                if error_type == "captcha":  # 需要验证码
                    code = self.solve_captcha()
                    data["_code"] = code
                    time.sleep(5)
                    return self.repost(oPost, extra_data=data)
                return False

        except Exception as e:
            self.logger.error(r.text)
            self.logger.error(e)
            return False
    
    def afterDumpPost(self, savePath):
        uploadFiles(savePath)  # 阻塞


if __name__ == '__main__':
    # todo 用argparser来处理
    sf = SubFunctions()
    dResult = {}
    try:
        if len(sys.argv) <= 1:
            lCmd = input("请输入命令").split()
        else:
            lCmd = sys.argv[1:]
        dResult = sf.selectFunc(*lCmd)
    except Exception as e:
        sf.logger.error(traceback.format_exc())
        dResult["ok"] = 0
        dResult["msg"] = str(e)
    print(json.dumps(dResult))
