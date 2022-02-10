import os
import sys

from bypy import ByPy

from MyLogger import getLogger


class MyByPy(ByPy):
    def __init__(self, *args, **kwargs):
        super(MyByPy, self).__init__(*args, **kwargs)
        self.logger = getLogger("ByPy")
    
    def pv(self, msg: str, **kwargs):
        self.logger.info(msg)
        return super().pv(msg, **kwargs)


def uploadFiles(filePath: str):
    bp = MyByPy()
    bp.upload(filePath, filePath)
    if sys.platform == "linux":
        os.system(f"rm -rf {filePath}")
