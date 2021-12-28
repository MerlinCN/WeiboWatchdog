from html.parser import HTMLParser
from typing import Union


class CPostTextParser(HTMLParser):
    def __init__(self):
        super(CPostTextParser, self).__init__()

        self.postText: str = ""

    def handle_starttag(self, tag: str, attrs):
        if tag == "br":
            self.postText += "\n"
        # print("Encountered a start tag:", tag)

    def handle_endtag(self, tag: str):
        if tag == "br":
            self.postText += "\n"
        # print("Encountered an end tag :", tag)

    def handle_data(self, data: str):
        self.postText += data
        # print("Encountered some data  :", data)

    def feed(self, data) -> str:
        super(CPostTextParser, self).feed(data)
        return self.postText


class CPost:
    def __init__(self, dPost: dict):
        self.RawData = dPost
        self.uid: int = dPost["id"]  # 微博uid
        self.userUid: int = dPost["user"]["id"]  # 博主uid
        self.userName: str = dPost["user"]["screen_name"]  # 博主名称
        self.text = dPost["text"]  # 微博内容
        self.createdTime: int = dPost["created_at"]  # 微博发送时间
        self.source: str = dPost["source"]  # 微博发送设备
        self.images: list[str] = [img["large"]["url"] for img in dPost.get("pics", [])]  # 微博图片
        self.extraTitle: dict[str:str] = dPost.get("title", {})  # 微博横幅
        self.onlyFans: bool = True if "仅粉丝可见" in self.extraTitle.values() else False  # 是否粉丝可见
        self.setTop: bool = True if "置顶" in self.extraTitle.values() else False  # 是否置顶
        dPageInfo = dPost.get("page_info", {})
        if dPageInfo.get("type", "") == "video" and dPageInfo.get("urls"):
            # 挺诡异的就是有的video没有urls属性，情况少见
            videoUrl = list(dPageInfo['urls'].values())[0]
            self.video: str = videoUrl  # 视频链接
        else:
            self.video = ""

        self.originPost: Union[CPost, None]
        if dPost.get("retweeted_status", {}) and dPost.get("retweeted_status", {}).get("user"):
            self.originPost: Union[CPost, None] = CPost(dPost["retweeted_status"])  # 转发的原博
        else:
            self.originPost: Union[CPost, None] = None
        self.livePhotos: list[str] = dPost.get("live_photo", [])

    def isOriginPost(self) -> bool:
        """
        是否是原创微博
            True : 原创
            False: 转发
        """
        if self.originPost is None:
            return True
        else:
            return False

    def Text(self) -> str:
        hp = CPostTextParser()
        text = hp.feed(self.text)
        text.replace("\n\n", "\n")
        hp.close()
        return text
