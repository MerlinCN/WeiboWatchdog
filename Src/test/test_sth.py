from Engine import SpiderEngine
from Post import CPost
from Util import raiseACall


def test_parse(url) -> CPost:
    wd = SpiderEngine(loggerName="Test")
    oPost = wd.parseOnePost(url)
    return oPost


def test_bark(context, url):
    raiseACall(context, url)


if __name__ == '__main__':
    # do something
    pass
