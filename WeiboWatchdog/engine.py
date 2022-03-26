import os
import random
import sqlite3
import sys

import requests

import bypy_tool
from WeiboBot.weibo import Weibo
from ai_tool import BaiduAPI
from log import get_logger
from util import read_special_users


class SpiderEngine:
    
    def __init__(self, loggerName: str):
        self.logger = get_logger(loggerName, module_name=__name__)
        self.ai_tool = BaiduAPI()
        self.conn = sqlite3.connect("history.db")
        self.initConn()
    
    # region 数据库操作
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
    
    # endregion
    
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
            bypy_tool.not_blocking_upload(savePath)
            return True
        else:
            if sys.platform == "linux":  # 清理文件 防止堆积
                os.system(f"rm -rf {savePath}")
            return False
    
    async def detection(self, oWeibo: Weibo) -> bool:
        """
        检测图片中的人来判断是否应该转发

        :param oWeibo:微博
        :return:是否应该转发
        """
        if not oWeibo.thumbnail_image_list():  # 用缩略图来做识别（API限制4M)
            return False
        for image in oWeibo.thumbnail_image_list():
            human_num = await self.ai_tool.detection(image, oWeibo)
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
        if oWeibo.original_weibo is None:
            if oWeibo.video_url():
                self.logger.info(f"微博带视频,不转发")
                await self.dump_post(oWeibo)
                return False
            if len(oWeibo.image_list()) < 3:
                self.logger.info(f"微博 图片数量小于3张,不转发")
                return False
            if oWeibo.full_text().find("房间号") > 0:  # 带直播链接的不转发
                self.logger.info(f"微博带直播链接,不转发")
                return False
            if not oWeibo.is_visible():
                self.logger.info(f"微博不可见,不转发")
                return False
            if await self.detection(oWeibo):
                return True
        else:
            lSp = read_special_users()
            if oWeibo.user_uid() in lSp:
                return True
            self.logger.info(f"非原创微博,不转发")
            return False
        return False
