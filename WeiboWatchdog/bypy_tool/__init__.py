import os
import sys
from multiprocessing import Process

from bypy import ByPy

from WeiboWatchdog.log import get_logger


class MyByPy(ByPy):
    def __init__(self, *args, **kwargs):
        super(MyByPy, self).__init__(*args, **kwargs)
        self.logger = get_logger("ByPy", module_name=__name__)

    def pv(self, msg: str, **kwargs):
        self.logger.info(msg)
        return super().pv(msg, **kwargs)


def upload_files(filePath: str):
    bp = MyByPy()
    if not os.path.exists(filePath):  # 多次转发的时候可能被另一个进程删除
        bp.logger.warning("文件夹不存在")
        return
    result = bp.upload(filePath, filePath)
    if result != 0:
        bp.logger.warning(f"{filePath} 上传失败")
    if sys.platform == "linux":
        os.system(f"rm -rf {filePath}")


def not_blocking_upload(filePath: str):
    p = Process(target=upload_files, args=(filePath,))  # 非阻塞，开个进程用于上传到云盘
    p.start()
