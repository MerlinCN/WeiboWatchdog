import os
import random
import sqlite3
import sys
from multiprocessing import Process

import requests

from AITool import CBaiduAPI
from MyLogger import getLogger
from PCS import uploadFiles
from Util import readSpecialUsers
from WeiboBot.weibo import Weibo


class SpiderEngine:
    
    def __init__(self, loggerName: str, printLog=True):
        self.logger = getLogger(loggerName, printLog)
        self.oAIAPI = CBaiduAPI()
        self.conn = sqlite3.connect("history.db")
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
    
    async def dump_post(self, oWeibo: Weibo, canDuplicable=False) -> bool:
        """
        保存微博，并且判断微博图片大小

        :param canDuplicable: 能否重复保存
        :param oWeibo: 微博
        :return: 是否应该转发
        """
        userName = oWeibo.user['screen_name']
        rootPath = f"Data/{userName}/{oWeibo.id}"
        videoPath = f"Video/{userName}/{oWeibo.id}"
        if oWeibo.video_url():
            savePath = videoPath
        else:
            savePath = rootPath
        iMaxImageSize = 0
        threshold = 1e6 * 0.4
        if not os.path.exists(savePath):
            os.makedirs(savePath)
        elif canDuplicable is False:
            return True
        contextName = f"{savePath}/{oWeibo.id}.txt"
        with open(contextName, 'w', encoding="utf8") as f:
            f.write(f"{userName}\n")
            f.write(f"{oWeibo.created_at}\n")
            f.write(oWeibo.text + '\n')
            for livePhoto in oWeibo.live_photo:
                f.write(livePhoto + '\n')
            if oWeibo.video_url():
                f.write(oWeibo.video_url())
        
        try:
            if oWeibo.video_url():
                video_res = requests.get(oWeibo.video_url())
                with open(f"{savePath}/{oWeibo.id}.mp4", 'wb') as f:
                    f.write(video_res.content)
                self.logger.info(f"保存微博视频成功")
        except Exception as e:
            self.logger.error(e)
        
        try:
            for idx, livePhoto in enumerate(oWeibo.live_photo):
                livePhoto_res = requests.get(livePhoto)
                with open(f"{savePath}/livephoto_{idx + 1}.mov", 'wb') as f:
                    f.write(livePhoto_res.content)
                self.logger.info(f"保存微博LivePhotos{idx + 1}成功")
        except Exception as e:
            self.logger.error(e)
        
        for idx, image in enumerate(oWeibo.image_list()):
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
        if iMaxImageSize < threshold and oWeibo.image_list():
            self.logger.info(f"图片最大size为{iMaxImageSize / 1e6}mb 小于{threshold / 1e6}mb")
        elif iMaxImageSize >= threshold:
            self.logger.info(f"图片最大size为{iMaxImageSize / 1e6}mb 大于等于{threshold / 1e6}mb")
        if iMaxImageSize >= threshold or oWeibo.live_photo or oWeibo.video_url() or canDuplicable:
            self.afterDumpPost(savePath)
            return True
        else:
            if sys.platform == "linux":
                os.system(f"rm -rf {savePath}")
            return False
    
    def afterDumpPost(self, savePath):
        p = Process(target=uploadFiles, args=(savePath,))  # 非阻塞，开个进程用于上传到云盘
        p.start()
    
    async def detection(self, oWeibo: Weibo) -> bool:
        """
        检测图片中的人来判断是否应该转发

        :param oWeibo:微博
        :return:是否应该转发
        """
        if not oWeibo.thumbnail_image_list():  # 用缩略图来做识别（API限制4M)
            return False
        for image in oWeibo.thumbnail_image_list():
            human_num = await self.oAIAPI.detection(image, oWeibo)
            if human_num >= 1:
                self.logger.info(f"微博 {oWeibo.detail_url()} 检测到人体 {human_num}")
                return True
        
        self.logger.info(f"微博 {oWeibo.detail_url()} 未检测到人体 ")
        return False
    
    @staticmethod
    def randomComment(oWeibo: Weibo) -> str:
        if len(oWeibo.image_list()) < 6:
            return "转发微博"
        
        lComments = ["[打call]", "[羞嗒嗒]", "[awsl]", "[赢牛奶]", "[心]", "[好喜欢]",
                     "[求关注]", "[哆啦A梦花心]", "[送花花]", "[彩虹屁]", "[哇]"]
        sComment = random.choice(lComments) * random.randint(1, 3)
        return sComment
    
    def is_had_scan(self, oWeibo: Weibo) -> bool:
        if oWeibo.original_weibo is None:
            isInScanHistory = self.isInScanHistory(oWeibo.weibo_id())
            if isInScanHistory:  # 单次扫描
                return True
            else:
                self.updateScanHistory(oWeibo.weibo_id())
        else:
            isInScanHistory = self.isInScanHistory(oWeibo.original_weibo.weibo_id())
            if isInScanHistory:  # 单次扫描
                return True
            else:
                self.updateScanHistory(oWeibo.original_weibo.weibo_id())
        return False

    async def is_repost(self, oWeibo: Weibo) -> bool:
        if self.is_had_scan(oWeibo) is True:
            return False
        self.logger.info(f"开始处理微博 {oWeibo.detail_url()}")
        if oWeibo.original_weibo is None:
            if len(oWeibo.image_list()) < 3:
                return False
            if oWeibo.full_text().find("房间号") > 0:  # 带直播链接的不转发
                return False
            if oWeibo.video_url():
                await self.dump_post(oWeibo)
                return False
            if not oWeibo.is_visible():
                return False
            if oWeibo.full_text().find("超话") > 0:  #
                return True
            if await self.detection(oWeibo):
                return True
        else:
            lSp = readSpecialUsers()
            if oWeibo.user_uid() in lSp:
                return True
            return False
        return False
