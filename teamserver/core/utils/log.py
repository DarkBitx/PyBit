import logging
from logging.handlers import RotatingFileHandler

# ======== Configuration ========
LOG_FILE = "server.log"
MAX_LOG_SIZE = 100 * 1024 * 1024
BACKUP_COUNT = 3

# ======== Create Logger ========
root_logger = logging.getLogger("main")
root_logger.setLevel(logging.DEBUG)

if not root_logger.handlers:
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT)
    file_format = logging.Formatter('%(asctime)s [%(name)s][%(levelname)s]  %(message)s')
    file_handler.setFormatter(file_format)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_format = logging.Formatter('[%(name)s][%(levelname)s] %(message)s')
    console_handler.setFormatter(console_format)
    console_handler.setLevel(logging.INFO)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

# ======== Logging Functions ========
def info(msg):
    root_logger.info(msg)

def warning(msg):
    root_logger.warning(msg)

def error(msg):
    root_logger.error(msg)

def debug(msg):
    root_logger.debug(msg)

def critical(msg):
    root_logger.critical(msg)

def exception(msg):
    root_logger.exception(msg)

def get_logger(name, file_only=False):
    new_logger = logging.getLogger(name)
    new_logger.setLevel(root_logger.level)

    if new_logger.hasHandlers():
        return new_logger

    if file_only:
        for handler in root_logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                new_logger.addHandler(handler)
    else:
        for handler in root_logger.handlers:
            new_logger.addHandler(handler)

    return new_logger



def set_level(level_name):
    level = getattr(logging, level_name.upper(), None)
    if isinstance(level, int):
        root_logger.setLevel(level)
        for handler in root_logger.handlers:
            handler.setLevel(level)

