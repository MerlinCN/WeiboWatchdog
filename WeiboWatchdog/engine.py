import os
import sys

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

import bypy_tool
import config
from WeiboBot.weibo import Weibo
from ai_tool import BaiduAPI
from log import get_logger


class SpiderEngine:

    def __init__(self, loggerName: str):
        self.logger = get_logger(loggerName, module_name=__name__)
        self.ai_tool = BaiduAPI()
        self.check_config()
        self.timeout = 60
        options = Options()
        options.add_argument("enable-automation")
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument("--dns-prefetch-disable")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        # options.add_argument('disable-infobars')
        self.options = options
        self.wd = None
        # self.wd.set_page_load_timeout(5)

    def check_config(self):
        if not config.cookies:
            self.logger.error("请先设置cookies")
            sys.exit(-1)
        if not config.bark_key:
            self.logger.info("未开启bark告警功能")
        if not config.ai_key or not config.ai_secret:
            self.logger.info("未开启AI人体识别功能")
        if config.is_repost:
            self.logger.info("开启转发功能")
        else:
            self.logger.info("未开启转发功能")
        if config.is_upload:
            self.logger.info("开启上传功能")
            os.system("bypy info")
        else:
            self.logger.info("未开启上传功能")

    async def dump_post(self, oWeibo: Weibo, is_force=False) -> bool:
        """
        保存微博，并且判断微博图片大小

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

        self.wd = webdriver.Chrome(options=self.options)

        screenshot = b''
        try:
            self.wd.get(oWeibo.detail_url())
            wait = WebDriverWait(self.wd, 30)
            wait.until(lambda _: self.wd.find_elements(By.CSS_SELECTOR, '.f-weibo'))
            weibo_frame = self.wd.find_element(By.CSS_SELECTOR, '.f-weibo')
            screenshot = weibo_frame.screenshot_as_png
        except Exception as e:
            self.logger.error(f"{oWeibo.detail_url()} webdriver错误 \n{e}")

        self.wd.quit()

        if screenshot:
            with open(f"{savePath}/{oWeibo.id}.png", "wb") as f:
                f.write(screenshot)
            self.logger.info(f"保存微博截图成功")

        else:
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
                video_res = requests.get(oWeibo.video_url(), timeout=self.timeout)
                with open(f"{savePath}/{oWeibo.id}.mp4", 'wb') as f:
                    f.write(video_res.content)
                self.logger.info(f"保存微博视频成功")
        except Exception as e:
            self.logger.error(e)

        try:
            for idx, livePhoto in enumerate(oWeibo.live_photo):
                livePhoto_res = requests.get(livePhoto, timeout=self.timeout)
                with open(f"{savePath}/{oWeibo.id}_{idx + 1}.mov", 'wb') as f:
                    f.write(livePhoto_res.content)
                self.logger.info(f"保存微博LivePhotos{idx + 1}成功")
        except Exception as e:
            self.logger.error(e)

        for idx, image in enumerate(oWeibo.image_list()):
            try:
                imageName = image.split('/').pop()
                res = requests.get(image, timeout=self.timeout)
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
        if is_force is True:
            bypy_tool.not_blocking_upload(savePath)
            return True
        if (iMaxImageSize >= threshold or oWeibo.live_photo or oWeibo.video_url()) and config.is_upload:
            bypy_tool.not_blocking_upload(savePath)
            return True
        else:
            if sys.platform == "linux":  # 清理文件 防止堆积
                os.system(f"rm -rf {savePath}")
            return False

    async def detection(self, oWeibo: Weibo) -> bool:
        """
        检测图片中的人来判断是否应该转发
        如果没有启动AI检测，则直接返回True

        :param oWeibo:微博
        :return:是否应该转发
        """
        if not oWeibo.thumbnail_image_list():  # 用缩略图来做识别（API限制4M)
            return False
        if self.ai_tool.is_enable is False:
            return True
        for image in oWeibo.thumbnail_image_list():
            human_num = await self.ai_tool.detection(image, oWeibo)
            if human_num >= 1:
                self.logger.info(f"微博 {oWeibo.detail_url()} 检测到人体 {human_num}")
                return True

        self.logger.info(f"微博 {oWeibo.detail_url()} 未检测到人体 ")
        return False

    async def is_process(self, oWeibo: Weibo) -> bool:
        if oWeibo.original_weibo is None:
            if oWeibo.video_url():
                self.logger.info(f"微博带视频,不继续处理")
                await self.dump_post(oWeibo)
                return False
            if len(oWeibo.image_list()) < 3:
                self.logger.info(f"微博 图片数量小于3张,不继续处理")
                return False
            if oWeibo.full_text().find("房间号") > 0:  # 带直播链接的不转发
                self.logger.info(f"微博带直播链接,不继续处理")
                return False
            if not oWeibo.is_visible():
                self.logger.info(f"微博不可见,不继续处理")
                return False
            if await self.detection(oWeibo):
                return True
        else:
            if oWeibo.user_uid() in config.special_users:
                return True
            if oWeibo.original_weibo.is_read is False and oWeibo.original_weibo.user_c.following:
                self.logger.info("检测转发微博原博")
                return await self.is_process(oWeibo.original_weibo)
            self.logger.info(f"非原创微博,不继续处理")
            return False
        return False
