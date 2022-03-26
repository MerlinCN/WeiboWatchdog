import sys
from typing import List

import requests

import config


def read_cookies():
    return config.Cookies


def bark_call(context, url=""):
    if not getattr(config, "BarkKey", None):
        return
    try:
        barkUrl = f"https://api.day.app/{config.BarkKey}/{context}"
        if url:
            barkUrl += f"?url={url}"
        requests.get(barkUrl)
    except Exception as e:
        pass


def read_special_users() -> List[int]:
    if not getattr(config, "SpUser", None):
        return []
    return config.SpUser


def read_ai_key():
    if getattr(config, "API_key", None) is None or getattr(config, "SecretKey", None) is None:
        return "", ""
    return config.API_key, config.SecretKey


def is_debug():
    return True if sys.gettrace() else False
