import json
import os
import random
import re
import sqlite3
import time
from typing import Dict

import requests

from Logger import getLogger
from Post import CPost
from Util import headers_raw_to_dict, readCookies


class WeiboDog:
    
    def __init__(self):
        self.logger = getLogger()
        self.mainSession = requests.session()
        self.conn = sqlite3.connect("history.db")
        self.header = headers_raw_to_dict(b'''
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
        self.thisPagePost: Dict[int, CPost] = {}
        self.st, self.uid = self.get_st()
        
        self.initConn()
    
    def initConn(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS history(
   mid VARCHAR(20),
   PRIMARY KEY(mid)
);''')
        cursor.close()
        self.conn.commit()
    
    def updateHistory(self, mid):
        cursor = self.conn.cursor()
        cursor.execute(f'''
        insert into history (mid) values ({mid});
        ''')
        cursor.close()
        self.conn.commit()
        self.logger.info(f"转发{mid}历史存库成功")
    
    def isInHistory(self, mid):
        cursor = self.conn.cursor()
        cursor.execute(f'''
        select * from history where mid = {mid};
        ''')
        
        values = cursor.fetchall()
        cursor.close()
        return len(values) > 0
    
    def get_header(self):
        return self.header
    
    def add_header_param(self, key, value):
        header = self.get_header()
        header[key] = value
        return header
    
    def add_ref(self, value):
        header = self.get_header()
        header["referer"] = value
        
        return self.add_header_param("referer", value)
    
    def get_st(self) -> tuple[str, int]:  # st是转发微博post必须的参数
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
        '''
        刷新主页
        :return:
        '''
        url = "https://m.weibo.cn/feed/friends?"
        header = self.add_ref(url)
        r = self.mainSession.get(url, headers=header)
        data = r.json()
        self.thisPagePost: Dict[int, CPost] = {}
        try:
            for dPost in data["data"]["statuses"]:
                _oPost = CPost(dPost)
                self.thisPagePost[_oPost.uid] = _oPost
        except Exception as e:
            self.logger.error(r.text)
            self.logger.error(e)
            time.sleep(10)
            self.refreshPage()
    
    def repost(self, oPost: CPost):
        st, _ = self.get_st()
        url = "https://m.weibo.cn/api/statuses/repost"
        content = "转发微博"
        mid = oPost.uid
        
        if oPost.onlyFans:
            self.logger.info(f"微博{mid} 仅粉丝可见，不可转载")
            return
        if self.isInHistory(mid):
            return
        data = {"id": mid, "content": content, "mid": mid, "st": st, "_spr": "screen:2560x1440"}
        # 这里一定要加referer， 不加会变成不合法的请求
        self.add_ref(f"https://m.weibo.cn/compose/repost?id={mid}")
        self.refeshToken()
        r = self.mainSession.post(url, data=data, headers=self.header)
        try:
            if r.json().get("ok") == 1:
                self.logger.info(f'转发微博{mid}成功')
                self.updateHistory(mid)
                self.dump_post(oPost)
                return True
            else:
                self.logger.info(f'转发微博{mid}失败 {r.text}')
                return False

        except Exception as e:
            self.logger.error(r.text)
            self.logger.error(e)

    def update_detail(self, oPost: CPost):
        url = f"https://m.weibo.cn/{oPost.userUid}/{oPost.uid}?"
        r = self.mainSession.get(url, headers=self.header)
        try:
            dDetail = json.loads(re.findall(r'(?<=render_data = \[)[\s\S]*(?=\]\[0\])', r.text)[0])
            if "pics" in dDetail["status"]:
                oPost.images = [d['large']['url'] for d in dDetail["status"]["pics"]]
            oPost.text = dDetail["status"]["text"]
        except Exception as e:
            self.logger.error(r.text)
            self.logger.error(e)

    def __del__(self):
        self.mainSession.close()
        handlers = self.logger.handlers[:]
        for handler in handlers:
            handler.close()
            self.logger.removeHandler(handler)
        self.conn.close()

    def dump_post(self, oPost: CPost):
        '''
        保存微博文章和图片 todo 异步下载
        :param oPost:
        :return:
        '''
        rootPath = f"Data/{oPost.userUid}/{oPost.uid}"
        if not os.path.exists(rootPath):
            os.makedirs(rootPath)
        contextName = f"{rootPath}/{oPost.uid}.txt"
        if oPost.Text().find("全文") > 0 or len(oPost.images) >= 9:
            self.update_detail(oPost)
        with open(contextName, 'w', encoding="utf8") as f:
            f.write(f"{oPost.userName}\n")
            f.write(f"{oPost.createdTime}\n")
            f.write(oPost.Text())
        self.logger.info(f"保存微博{oPost.uid}内容成功")
    
        for idx, image in enumerate(oPost.images):
            try:
                imageName = image.split('/').pop()
                res = requests.get(image)
                with open(f"{rootPath}/{imageName}", 'wb') as f:
                    f.write(res.content)
            except Exception as e:
                self.logger.error(e)
            self.logger.info(f"保存微博{oPost.uid}图片{idx + 1}成功")


if __name__ == '__main__':
    wd = WeiboDog()
    while 1:
        wd.refreshPage()
        for oPost in wd.thisPagePost.values():
            if oPost.isOriginPost() and len(oPost.images) >= 3:
                wd.repost(oPost)
            elif not oPost.isOriginPost() and len(oPost.originPost.images) >= 9:
                wd.repost(oPost.originPost)
        interval = random.randint(10, 20)
        wd.logger.info("Heartbeat")
        time.sleep(interval)
