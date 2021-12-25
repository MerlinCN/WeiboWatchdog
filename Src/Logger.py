import logging
import logging.handlers
import os
import sys
import time


def getLogger():
    logger = logging.getLogger("WeiboDog")
    
    s_handler = logging.StreamHandler(sys.stdout)
    s_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s[:%(lineno)d] - %(message)s"))
    log_path = "Log"
    if not os.path.exists(log_path):
        os.mkdir(log_path)
    f_handler = logging.handlers.TimedRotatingFileHandler(log_path + '/Main', encoding='utf8')
    f_handler.suffix = "%Y%m%d_%H.log"
    f_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s[:%(lineno)d] - %(message)s"))
    f_handler.doRollover()
    logger.addHandler(s_handler)
    logger.addHandler(f_handler)
    logger.setLevel(logging.DEBUG)
    return logger


if __name__ == '__main__':
    logger = getLogger()
    while 1:
        logger.info("Test")
        logger.error("Test")
        time.sleep(1)
