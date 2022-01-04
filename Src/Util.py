from typing import Dict, List

import requests

import Config


def headers_raw_to_dict(headers_raw: bytes) -> Dict[str, str]:
    """
    复制浏览器中的header
    """
    if headers_raw is None:
        raise ValueError("不能为空")
    headers = headers_raw.splitlines()
    headers_tuples = [header.split(b":", 1) for header in headers]
    
    result_dict = {}
    for header_item in headers_tuples:
        if not len(header_item) == 2:
            continue

        item_key: str = header_item[0].strip().decode("utf8")
        item_value: str = header_item[1].strip().decode("utf8")
        result_dict[item_key] = item_value
    
    return result_dict


def readCookies():
    if Config.Cookies == b"":
        raise Exception("请填入Cookies")
    return Config.Cookies


def raiseACall(context):
    if not getattr(Config, "BarkKey", None):
        return
    requests.get(f"https://api.day.app/{Config.BarkKey}/{context}")


def sp_user() -> List[int]:
    if not getattr(Config, "SpUser", None):
        return []
    return Config.SpUser


def get_ai_key():
    if getattr(Config, "API_key", None) is None or getattr(Config, "SecretKey", None) is None:
        return "", ""
    return Config.API_key, Config.SecretKey
