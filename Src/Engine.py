import json
import os
import random
import re
import sqlite3
import time
from multiprocessing import Process
from threading import Timer
from typing import Dict, Union, Tuple

import ddddocr
import requests

from AITool import CBaiduAPI
from MyLogger import getLogger
from PCS import uploadFiles
from Post import CPost
from Util import byte2Headers, readCookies, raiseACall


class SpiderEngine:
    
    def __init__(self, loggerName: str):
        self.logger = getLogger(loggerName)
        self.oAIAPI = CBaiduAPI()
        self.mainSession = requests.session()
        self.conn = sqlite3.connect("history.db")
        self.header: Dict[str, Union[str, int]]
        self.header = byte2Headers(b'''
        accept: application/json, text/plain, */*
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cookie: %b
mweibo-pwa: 1
referer: https://m.weibo.cn/
sec-ch-ua: " Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "Windows"
sec-fetch-dest: empty
sec-fetch-mode: cors
sec-fetch-site: same-origin
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36
x-requested-with: XMLHttpRequest
x-xsrf-token: 1d1b9c
        ''' % readCookies())
        
        self.cookies = self.header["cookie"]
        self.thisPagePost: Dict[int, CPost] = {}  # 主页的微博
        self.thisRecommendPagePost: Dict[int, CPost] = {}  # 热门推荐的微博
        self.st, self.uid = self.get_st()
        self.allowPost = True
        self.initConn()
    
    def initConn(self):
        """
        初始化表
        """
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS history(
   mid VARCHAR(20),
   PRIMARY KEY(mid)
);''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ScanHistory(
       mid VARCHAR(20) PRIMARY KEY
    );''')
        cursor.close()
        self.conn.commit()
    
    def updateHistory(self, mid: int):
        """
        更新转发历史
        """
        cursor = self.conn.cursor()
        cursor.execute(f'''
        insert into history (mid) values ({mid});
        ''')
        cursor.close()
        self.conn.commit()
        self.logger.info(f"转发历史存库成功")
    
    def updateScanHistory(self, mid: int):
        """
        更新扫描历史
        """
        cursor = self.conn.cursor()
        cursor.execute(f"insert into ScanHistory (mid) values ({mid});")
        cursor.close()
        self.conn.commit()
    
    def isInHistory(self, mid: int) -> bool:
        """
        是否已经转发

        :param mid: 微博编号
        :return: 结果
        """
        cursor = self.conn.cursor()
        cursor.execute(f'''
        select * from history where mid = {mid};
        ''')
        
        values = cursor.fetchall()
        cursor.close()
        return len(values) > 0
    
    def isInScanHistory(self, mid: int) -> bool:
        """
        是否已经扫描

        :param mid: 微博编号
        :return: 结果
        """
        cursor = self.conn.cursor()
        cursor.execute(f'''
                select * from ScanHistory where mid = {mid};
                ''')
        values = cursor.fetchall()
        cursor.close()
        return len(values) > 0
    
    def get_header(self) -> Dict[str, Union[str, int]]:
        return self.header
    
    def add_header_param(self, key: str, value: str) -> Dict[str, Union[str, int]]:
        header = self.get_header()
        header[key] = value
        return header
    
    def add_ref(self, value: str) -> Dict[str, Union[str, int]]:
        return self.add_header_param("referer", value)
    
    def get_st(self) -> Tuple[str, int]:
        """
        获得session token

        :return: session token和当前用户uid
        """
        url = "https://m.weibo.cn/api/config"
        header = self.add_ref(url)
        r = self.mainSession.get(url, headers=header)
        data = r.json()
        isLogin = data['data']['login']
        if not isLogin:
            raise Exception("未登录")
        st = data["data"]["st"]
        uid = int(data['data']['uid'])
        return st, uid
    
    def refeshToken(self):
        st, _ = self.get_st()
        self.header["x-xsrf-token"] = st
        return self.header
    
    def refreshPage(self):
        """
        刷新主页
        """
        st, _ = self.get_st()
        url = "https://m.weibo.cn/feed/friends?"
        header = self.add_ref("https://m.weibo.cn/")
        self.header["x-xsrf-token"] = st
        r = self.mainSession.get(url, headers=header)
        data = r.json()
        self.thisPagePost = {}
        try:
            if r.json().get("ok") == 1:
                for dPost in data["data"]["statuses"]:
                    _oPost = CPost(dPost)
                    self.thisPagePost[_oPost.uid] = _oPost
                return True
            else:
                self.logger.error(f"刷新主页失败 err = {data}")
                return False
        except Exception as e:
            self.logger.error(data)
            self.logger.error(e)
            time.sleep(30)
            self.refreshPage()
    
    def refreshRecommend(self):
        """
        刷新热门推荐（会包含广告）

        :return:是否成功
        """
        st, _ = self.get_st()
        url = "https://m.weibo.cn/api/container/getIndex?containerid=102803&openApp=0"
        header = self.add_ref("https://m.weibo.cn/")
        self.header["x-xsrf-token"] = st
        r = self.mainSession.get(url, headers=header)
        data = r.json()
        self.thisRecommendPagePost = {}
        try:
            if r.json().get("ok") == 1:
                for dPost in data["data"]["cards"]:
                    _oPost = CPost(dPost["mblog"], isRecommend=True)
                    self.thisRecommendPagePost[_oPost.uid] = _oPost
                return True
            else:
                self.logger.error(f"刷新热门失败 err = {data}")
                return False
        except Exception as e:
            self.logger.error(data)
            self.logger.error(e)
            time.sleep(60)
            self.refreshRecommend()
    
    def like(self, oPost: CPost) -> bool:
        """
        点赞

        :param oPost: 微博
        :return: 是否成功
        """
        st, _ = self.get_st()
        mid = oPost.uid
        url = "https://m.weibo.cn/api/attitudes/create"
        data = {"id": mid, "attitude": "heart", "st": st, "_spr": "screen:2560x1440"}
        self.add_ref(f"https://m.weibo.cn")
        self.header["x-xsrf-token"] = st
        r = self.mainSession.post(url, data=data, headers=self.header)
        try:
            if r.json().get("ok") == 1:
                self.logger.info(f'点赞成功')
                return True
            else:
                self.logger.error(f'点赞失败')
                return False
        except Exception as e:
            self.logger.error(r.json())
            self.logger.error(e)
    
    def startRepost(self, oPost: CPost):
        """
        开始转发微博

        :param oPost: 微博
        :return: 是否成功
        """
        bResult = self.repost(oPost)
        self.logger.info(f"结束处理{oPost.userName}（{oPost.userUid}）的微博 {self.postDetail(oPost)}")
        return bResult
    
    def repost(self, oPost: CPost, extra_data=None) -> bool:
        """
        转发微博

        :param oPost: 微博
        :param extra_data: 包含验证码的载荷
        :return: 是否成功
        """
        st, _ = self.get_st()
        url = "https://m.weibo.cn/api/statuses/repost"
        content = "转发微博"
        mid = oPost.uid
        if self.isInHistory(mid):
            return False
        if not extra_data:
            data = {"id": mid, "content": content, "mid": mid, "st": st, "_spr": "screen:2560x1440"}
            self.logger.info(f"开始处理{oPost.userName}（{oPost.userUid}）的微博 {self.postDetail(oPost)}")
        else:
            data = extra_data

        repostable = self.dump_post(oPost)
        if not repostable:
            self.logger.info(f"微博太小，不转载。")
            self.updateHistory(mid)
            return False
        if oPost.onlyFans:
            self.logger.info(f"微博仅粉丝可见，不可转载。")
            self.updateHistory(mid)
            return False
        if self.allowPost is False:
            self.logger.info(f"不转载状态")
            return False
        if len(oPost.images) >= 6:
            data["content"] = self.randomComment()
            data["dualPost"] = 1
        # 这里一定要加referer， 不加会变成不合法的请求
        self.add_ref(f"https://m.weibo.cn/compose/repost?id={mid}")
        self.header["x-xsrf-token"] = st
        r = self.mainSession.post(url, data=data, headers=self.header)
        if r.status_code != 200:  # 转发过多后
            self.logger.error("请求错误，开始休眠5分钟")
            time.sleep(60 * 5)  # 5分钟一个单位
            return self.repost(oPost, extra_data=data)
        try:
            if r.json().get("ok") == 1:
                self.logger.info(f'转发微博成功')
                self.updateHistory(mid)
                self.like(oPost)
                time.sleep(10)
                return True
            else:
                err = r.json()
                error_type = err["error_type"]
                errno = err["errno"]
                if error_type == "captcha":  # 需要验证码
                    code = self.solve_captcha()
                    data["_code"] = code
                    time.sleep(5)
                    return self.repost(oPost, extra_data=data)
                self.logger.error(
                    f'转发微博失败 \n {err["msg"]} \n {r.json()}')
                raiseACall(f'转发微博失败 {err["msg"]}')
                if errno == '20016':  # 转发频率过高，等一会儿就好
                    self.allowPost = False
                    tm = Timer(60 * 30, self.openAllow, args=[self])
                    tm.start()
                    return self.repost(oPost, extra_data=data)
                else:
                    time.sleep(30)
                return False

        except Exception as e:
            self.logger.error(r.text)
            self.logger.error(e)
            return self.repost(oPost, extra_data=data)

    def openAllow(self):
        self.allowPost = True

    def solve_captcha(self) -> str:
        """
        处理验证码

        :return: 验证码识别结果（30%左右成功，但可多次尝试）
        """
        nowTime = int(time.time() * 1000)
        url = f"https://m.weibo.cn/api/captcha/show?t={nowTime}"
        self.add_ref("https://m.weibo.cn/sw.js")
        res = self.mainSession.get(url, headers=self.header)
        ocr = ddddocr.DdddOcr(show_ad=False)
        result = ocr.classification(res.content)
        self.logger.info(f"识别验证码为:{result}")
        if len(result) != 4:
            self.solve_captcha()
        else:
            return result
    
    def update_detail(self, oPost: CPost) -> bool:
        """
        更新全文

        :param oPost: 微博
        :return: 是否成功
        """
        mid = oPost.uid
        url = f"https://m.weibo.cn/statuses/extend?id={mid}"
        st, _ = self.get_st()
        self.add_ref(f"https://m.weibo.cn/status/{mid}")
        self.header["x-xsrf-token"] = st
        r = self.mainSession.get(url, headers=self.header)
        responseJson = r.json()
        try:
            if responseJson.get("ok") == 1:
                self.logger.info(f'更新全文成功')
                oPost.text = responseJson["data"]["longTextContent"]
                return True
            else:
                self.logger.error(f'更新全文失败')
                return False
        except Exception as e:
            self.logger.error(responseJson)
            self.logger.error(e)
    
    def dump_post(self, oPost: CPost, canDuplicable=False) -> bool:
        """
        保存微博，并且判断微博图片大小

        :param canDuplicable: 能否重复保存
        :param oPost: 微博
        :return: 是否应该转发
        """
        rootPath = f"Data/{oPost.userName}/{oPost.uid}"
        videoPath = f"Video/{oPost.userName}/{oPost.uid}"
        if oPost.video:
            savePath = videoPath
        else:
            savePath = rootPath
        iMaxImageSize = 0
        threshold = 1e6 * 0.4
        if not os.path.exists(savePath):
            os.makedirs(savePath)
        elif canDuplicable is False:
            return True
        contextName = f"{savePath}/{oPost.uid}.txt"
        if oPost.Text().find("全文") > 0:
            self.update_detail(oPost)
        with open(contextName, 'w', encoding="utf8") as f:
            f.write(f"{oPost.userName}\n")
            f.write(f"{oPost.createdTime}\n")
            f.write(oPost.Text() + '\n')
            for livePhoto in oPost.livePhotos:
                f.write(livePhoto + '\n')
            if oPost.video:
                f.write(oPost.video)
        
        try:
            if oPost.video:
                video_res = requests.get(oPost.video)
                with open(f"{savePath}/{oPost.uid}.mp4", 'wb') as f:
                    f.write(video_res.content)
                self.logger.info(f"保存微博视频成功")
        except Exception as e:
            self.logger.error(e)
        
        try:
            for idx, livePhoto in enumerate(oPost.livePhotos):
                livePhoto_res = requests.get(livePhoto)
                with open(f"{savePath}/livephoto_{idx + 1}.mov", 'wb') as f:
                    f.write(livePhoto_res.content)
                self.logger.info(f"保存微博LivePhotos{idx + 1}成功")
        except Exception as e:
            self.logger.error(e)
        
        for idx, image in enumerate(oPost.images):
            try:
                imageName = image.split('/').pop()
                res = requests.get(image)
                with open(f"{savePath}/{imageName}", 'wb') as f:
                    iImageSize = len(res.content)
                    if iImageSize > iMaxImageSize:
                        iMaxImageSize = iImageSize
                    f.write(res.content)
            except Exception as e:
                self.logger.error(e)
            self.logger.info(f"保存微博图片{idx + 1}成功")

        self.logger.info(f"保存微博内容成功")
        if iMaxImageSize < threshold and oPost.images:
            self.logger.info(f"图片最大size为{iMaxImageSize / 1e6}mb 小于{threshold / 1e6}mb")
        elif iMaxImageSize >= threshold:
            self.logger.info(f"图片最大size为{iMaxImageSize / 1e6}mb 大于等于{threshold / 1e6}mb")
        if iMaxImageSize >= threshold or oPost.livePhotos or oPost.video:
            self.afterDumpPost(savePath)
            return True
        else:
            return False

    def afterDumpPost(self, savePath):
        p = Process(target=uploadFiles, args=(savePath,))  # 非阻塞，开个进程用于上传到云盘
        p.start()

    def detection(self, oPost: CPost) -> bool:
        """
        检测图片中的人和男人数来判断是否应该转发

        :param oPost:微博
        :return:是否应该转发
        """
        if not oPost.thumbnail_images:  # 用缩略图来做识别（API限制4M)
            return False
        isInScanHistory = self.isInScanHistory(oPost.uid)
        if isInScanHistory:  # 单次扫描
            return False
        else:
            self.updateScanHistory(oPost.uid)
        for image in oPost.thumbnail_images:
            human_num, male_num = self.oAIAPI.detection(image, oPost.isRecommend)
            if male_num >= 1 and oPost.isRecommend is True:  # 如果走热门推荐的话就不转发有男性的
                return False
            if human_num >= 1:
                self.logger.info(f"微博 {self.postDetail(oPost)} 检测到人体 {human_num}")
                return True
        
        self.logger.info(f"微博 {self.postDetail(oPost)} 未检测到人体 ")
        return False
    
    def parseOnePost(self, sPostUrl: str) -> Union[CPost, None]:
        if sPostUrl.isdigit():
            sUrl = f"https://m.weibo.cn/detail/{sPostUrl}"
        else:
            sUrl = sPostUrl
        try:
            r = self.mainSession.get(sUrl, headers=self.header)
            dPost = json.loads(re.findall(r'(?<=render_data = \[)[\s\S]*(?=\]\[0\])', r.text)[0])["status"]
            oPost = CPost(dPost)
        except Exception as e:
            self.logger.error(e)
            return None
        return oPost
    
    @staticmethod
    def postDetail(oPost: CPost) -> str:
        return f"https://m.weibo.cn/detail/{oPost.uid}"
    
    @staticmethod
    def randomComment() -> str:
        lComments = ["[打call]", "[羞嗒嗒]", "[awsl]", "[赢牛奶]", "[心]", "[好喜欢]", "[求关注]", "[哆啦A梦花心]"]
        sComment = random.choice(lComments) * random.randint(1, 3)
        return sComment
