import sys
from typing import List

import requests

import Config


def readCookies():
    if Config.Cookies == b"":
        raise Exception("请填入Cookies")
    return Config.Cookies


def barkCall(context, url=""):
    if not getattr(Config, "BarkKey", None):
        return
    try:
        barkUrl = f"https://api.day.app/{Config.BarkKey}/{context}"
        if url:
            barkUrl += f"?url={url}"
        requests.get(barkUrl)
    except Exception as e:
        pass


def readSpecialUsers() -> List[int]:
    if not getattr(Config, "SpUser", None):
        return []
    return Config.SpUser


def readAIKey():
    if getattr(Config, "API_key", None) is None or getattr(Config, "SecretKey", None) is None:
        return "", ""
    return Config.API_key, Config.SecretKey


def is_debug():
    return True if sys.gettrace() else False
