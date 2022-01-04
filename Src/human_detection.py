import base64

import requests

from Logger import getLogger
from Util import get_ai_key, raiseACall


class CAPI:
    def __init__(self):
        self.session = requests.session()
        self.logger = getLogger()
        api_key, secrets_key = get_ai_key()
        root_key = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secrets_key}"
        root_res = self.session.get(root_key)
        self.access_token = root_res.json()["access_token"]
        self.header = {'content-type': 'application/x-www-form-urlencoded'}
        self.detection_url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/body_attr"
    
    def detection(self, image_url) -> int:
        res_image = self.session.get(image_url)
        if res_image.status_code != 200:
            raiseACall(f"人体识别出错 {image_url}")
            return 0
        data = {"access_token": self.access_token, "image": base64.b64encode(res_image.content)}
        res_ai = requests.post(self.detection_url, data=data, headers=self.header)
        res_ai_json = res_ai.json()
        try:
            person_num = res_ai_json["person_num"]
            return person_num
        except Exception as e:
            self.logger.error(res_ai_json)
            self.logger.error(e)
            raiseACall(f"人体识别出错 {res_ai_json}")
            return 0
