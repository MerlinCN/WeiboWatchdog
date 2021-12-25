from Config import *


def headers_raw_to_dict(headers_raw):
    if headers_raw is None:
        return None
    headers = headers_raw.splitlines()
    headers_tuples = [header.split(b":", 1) for header in headers]
    
    result_dict = {}
    for header_item in headers_tuples:
        if not len(header_item) == 2:
            continue
        
        item_key = header_item[0].strip().decode("utf8")
        item_value = header_item[1].strip().decode("utf8")
        result_dict[item_key] = item_value
    
    return result_dict


def readCookies():
    if Cookies == b"":
        raise Exception("请填入Cookies")
    return Cookies
