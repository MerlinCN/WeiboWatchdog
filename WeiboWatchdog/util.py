import sys

import requests

import config


def bark_call(context, url=""):
    if not config.bark_key:
        return
    try:
        barkUrl = f"https://api.day.app/{config.bark_key}/{context}"
        if url:
            barkUrl += f"?url={url}"
        requests.get(barkUrl)
    except Exception as e:
        pass


def is_debug():
    return True if sys.gettrace() else False
