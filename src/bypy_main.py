from bypy import ByPy
from bypy.const import ENoError
from loguru import logger
from fastapi import FastAPI
from pathlib import Path
import shutil
from multiprocessing import Process

app = FastAPI()


def upload_to_bypy(path: str, remote_path: str):
    """在后台线程中执行上传任务"""
    try:
        bp = ByPy()
        path_obj = Path(path)
        if not path_obj.exists():
            logger.error(f"文件不存在: {path}")
            return False

        result = bp.upload(str(path_obj), str(remote_path))
        if result != ENoError:
            logger.error(f"上传失败: {result}")
            return False

        logger.info(f"上传成功: {path}")

        # 上传成功后删除本地文件
        if path_obj.is_file():
            path_obj.unlink()
        elif path_obj.is_dir():
            shutil.rmtree(path_obj)

        return True
    except Exception as e:
        logger.error(f"上传过程中发生错误: {e}")
        return False


def upload_in_process(path: str, remote_path: str):
    """在独立进程中执行上传任务"""
    upload_to_bypy(path, remote_path)


@app.get("/upload")
async def upload_process(path: str, remote_path: str):
    """多进程上传接口，立即返回，上传在独立进程中进行"""
    logger.info(f"启动多进程上传任务: {path} -> {remote_path}")
    p = Process(target=upload_in_process, args=(path, remote_path))
    p.start()
