from bypy import ByPy


def uploadFiles(filePath: str):
    bp = ByPy()
    bp.upload(filePath, filePath)
