import json
import os

cookies = ""  # m.weibo.cn cookie
bark_key = ""  #
special_users = []  # 只转发的用户
ai_key = ""  # 百度云人体识别api key 如果这个和下面的ai_secret为空，则不进行人体识别
ai_secret = ""  # 百度云人体识别api secret
is_repost = False  # 是否转发
is_upload = False  # 是否上传图片
is_screenshot = False  # 是否自动截图（需要自行配置chromedriver）

default_config = {
    "cookies": cookies,
    "bark_key": bark_key,
    "special_users": special_users,
    "ai_key": ai_key,
    "ai_secret": ai_secret,
    "is_repost": is_repost,
    "is_upload": is_upload,
    "is_screenshot": is_screenshot,
}

if not os.path.exists("config.json"):
    with open("config.json", "w") as f:
        f.write(json.dumps(default_config, indent=4))

with open("config.json", "r") as f:
    config = json.loads(f.read())
    for k, v in default_config.items():
        if k not in config:
            config[k] = v
    for k, v in config.items():
        globals()[k] = v

with open("config.json", "w") as f:
    f.write(json.dumps(config, indent=4))
