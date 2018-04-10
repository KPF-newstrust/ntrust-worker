import datetime
import logging

from . import mongo

worker_id = "(NotSet)"

coll_evtlog = None

EVTLOG_LEVEL_TRACE = 1
EVTLOG_LEVEL_DEBUG = 3
EVTLOG_LEVEL_INFO = 5
EVTLOG_LEVEL_WARNING = 6
EVTLOG_LEVEL_ERROR = 7
EVTLOG_LEVEL_FATAL = 9


def set_worker_id(wkid):
    global worker_id, coll_evtlog
    worker_id = wkid
    coll_evtlog = mongo.get_collection("evtlog")

LOCAL_ECHO_BACK = False

def enable_local_echo():
    global LOCAL_ECHO_BACK
    LOCAL_ECHO_BACK = True
    logging.basicConfig(level=logging.DEBUG)


def _save_event(level,msg):
    if coll_evtlog is None:
        raise SystemExit("eventlog.set_worker_id not ready")
    res = coll_evtlog.insert_one({"ts":datetime.datetime.utcnow(), "lv":level, "ip":"cluster", "tag":worker_id, "msg":msg})
    if not res.acknowledged:
        logging.error("EventLog(%d) failed: %s" % (level,msg))


def trace(msg):
    _save_event(EVTLOG_LEVEL_TRACE, msg)
    if LOCAL_ECHO_BACK:
        print(msg)

def debug(msg):
    _save_event(EVTLOG_LEVEL_DEBUG, msg)
    if LOCAL_ECHO_BACK:
        logging.debug(msg)

def info(msg):
    _save_event(EVTLOG_LEVEL_INFO, msg)
    if LOCAL_ECHO_BACK:
        logging.info(msg)

def warning(msg):
    _save_event(EVTLOG_LEVEL_WARNING, msg)
    if LOCAL_ECHO_BACK:
        logging.warning(msg)

def error(msg):
    _save_event(EVTLOG_LEVEL_ERROR, msg)
    if LOCAL_ECHO_BACK:
        logging.error(msg)

def fatal(msg):
    _save_event(EVTLOG_LEVEL_FATAL, msg)
    if LOCAL_ECHO_BACK:
        logging.error(msg)