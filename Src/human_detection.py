import base64
from typing import Tuple

import requests

from Logger import getLogger
from Util import get_ai_key, raiseACall


class CAPI:  # 百度人体识别API
    def __init__(self):
        self.session = requests.session()
        self.logger = getLogger()
        api_key, secrets_key = get_ai_key()
        root_key = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secrets_key}"
        root_res = self.session.get(root_key)
        self.access_token = root_res.json()["access_token"]
        self.header = {'content-type': 'application/x-www-form-urlencoded'}
        self.detection_url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/body_attr"
    
    def detection(self, image_url: str, bStrict=False) -> Tuple[int, int]:
        res_image = self.session.get(image_url)
        person_num = 0
        male_num = 0
        if res_image.status_code != 200:  # QPS过高
            raiseACall(f"人体识别出错 {image_url}")
            return person_num, male_num
        data = {"access_token": self.access_token, "image": base64.b64encode(res_image.content)}
        res_ai = requests.post(self.detection_url, data=data, headers=self.header)
        res_ai_json = res_ai.json()
        try:
            # 先看多少人，在看男性人数
            person_num_o = res_ai_json["person_num"]
            if person_num_o >= 1:
                person_info = res_ai_json["person_info"]
                for person in person_info:
                    if person['attributes']['gender']["name"] == "男性":
                        male_num += 1
                        if bStrict is True:
                            self.logger.info(f"{image_url} 检测到男性 跳过 ")
                            return person_num, male_num
                    if person['attributes']['is_human']["score"] >= 0.7 and person['attributes']['is_human'][
                        "name"] == "正常人体":
                        person_num += 1
            return person_num, male_num
        except Exception as e:
            self.logger.error(res_ai_json)
            self.logger.error(e)
            raiseACall(f"人体识别出错 {res_ai_json}")
            return person_num, male_num
