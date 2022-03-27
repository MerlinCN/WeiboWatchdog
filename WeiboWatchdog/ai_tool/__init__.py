import base64

import requests

from WeiboBot import Weibo
from log import get_logger
from util import read_ai_key, bark_call


class BaiduAPI:  # 百度人体识别API
    def __init__(self):
        self.session = requests.session()
        self.logger = get_logger("MainLoop", module_name=__name__)
        api_key, secrets_key = read_ai_key()
        root_key = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secrets_key}"
        root_res = self.session.get(root_key)
        self.access_token = root_res.json()["access_token"]
        self.header = {'content-type': 'application/x-www-form-urlencoded'}
        self.detection_url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/body_attr"
    
    async def detection(self, image_url: str, oWeibo: Weibo) -> int:
        res_image = self.session.get(image_url)
        person_num = 0
        if res_image.status_code != 200:  # QPS过高
            bark_call(f"人体识别出错 {image_url}")
            return person_num
        params = {"access_token": self.access_token, "image": base64.b64encode(res_image.content)}
        result = requests.post(self.detection_url, data=params, headers=self.header)
        try:
            data = result.json()
        except Exception as e:
            self.logger.error(result.status_code, result.text)
            bark_call(f"人体识别出错 {result.text}", oWeibo.scheme)
            self.logger.error(e)
            return person_num
        person_num_o = data["person_num"]
        if person_num_o >= 1:
            person_info = data["person_info"]
            for person in person_info:
                if person['attributes']['is_human']["score"] >= 0.7 \
                        and person['attributes']['is_human']["name"] == "正常人体":
                    person_num += 1
        return person_num
