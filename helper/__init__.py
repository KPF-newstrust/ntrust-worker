import logging
import sys
import pytz

if sys.version_info[0] < 3:
    raise SystemExit("Python 3 is required.")

"""
# LOGGING seutp
#logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s", datefmt='%Y-%m-%d %H:%M:%S')

def get_logger(name, omitname=False, level=logging.DEBUG):
    handler = logging.StreamHandler()
    if omitname:
        fmt = "%(asctime)s %(levelname)s %(message)s"
    else:
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    handler.setFormatter(logging.Formatter(fmt, datefmt='%Y-%m-%d %H:%M:%S'))

    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False

    return logger
"""

KOREA_TZ = pytz.timezone("Asia/Seoul")

def native_to_utc(native_dt):
    if native_dt is None:
        return None
    local_dt = KOREA_TZ.localize(native_dt, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt

from . import mongo
from . import rabbit
from . import eventlog

