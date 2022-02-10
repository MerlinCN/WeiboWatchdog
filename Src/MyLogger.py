import logging
import logging.handlers
import os
import sys
from logging import Logger


def initLogger(myLogger: Logger):
    s_handler = logging.StreamHandler(sys.stdout)
    s_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s[:%(lineno)d] - %(message)s"))
    log_path = f"Log/{myLogger.name}/"
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    f_handler = logging.handlers.TimedRotatingFileHandler(log_path + '/Main', encoding='utf8')
    f_handler.suffix = "%Y%m%d_%H.log"
    f_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s[:%(lineno)d] - %(message)s"))
    f_handler.doRollover()
    myLogger.addHandler(s_handler)
    myLogger.addHandler(f_handler)
    myLogger.setLevel(logging.DEBUG)
    setattr(myLogger, "isInit", True)


def getLogger(loggerName: str) -> Logger:
    logger = logging.getLogger(loggerName)
    if getattr(logger, "isInit", False) is False:
        initLogger(logger)
    
    return logger
