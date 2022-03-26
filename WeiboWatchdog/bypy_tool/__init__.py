import os
import sys
from multiprocessing import Process

from bypy import ByPy

from log import get_logger


class MyByPy(ByPy):
    def __init__(self, *args, **kwargs):
        super(MyByPy, self).__init__(*args, **kwargs)
        self.logger = get_logger("ByPy", module_name=__name__)
    
    def pv(self, msg: str, **kwargs):
        self.logger.info(msg)
        return super().pv(msg, **kwargs)


def upload_files(filePath: str):
    bp = MyByPy()
    bp.upload(filePath, filePath)
    if sys.platform == "linux":
        os.system(f"rm -rf {filePath}")


def not_blocking_upload(filePath: str):
    p = Process(target=upload_files, args=(filePath,))  # 非阻塞，开个进程用于上传到云盘
    p.start()
