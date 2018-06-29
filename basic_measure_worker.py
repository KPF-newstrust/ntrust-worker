#!/usr/bin/env python3

import os
import sys
import json
import configparser
import logging
import logging.config
import traceback

# install required package if in docker
if os.geteuid() == 0:
    import pkgutil
    import subprocess
    required_pkgs = ["pytz"]
    for pkg in required_pkgs:
        if not pkgutil.find_loader(pkg):
            p = subprocess.Popen(["pip3","install", pkg], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.wait()


import helper
import handler_basic
import handler_byline
import handler_lab
import handler_score

APP_VERSION = 4

if "WORKER_ID" in os.environ:
    WORKER_ID = os.environ["WORKER_ID"]
else:
    raise SystemExit("Environment variable 'WORKER_ID' is not found.")

if WORKER_ID == "dev":
    logging.config.fileConfig('logging.conf')
    helper.eventlog.enable_local_echo()

logger = logging.getLogger("basic")

helper.mongo.connect()

def update_self_then_restart():
    helper.mongo.close()
    if WORKER_ID == "dev":
        raise SystemExit("NoUpdate if dev")

    #script_path = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "gitpull_then_restart.sh")
    #subprocess.Popen([script_path])
    #raise SystemExit("Exit for self-update")

    # return code 99 will execute "git pull"
    print("Exit for update and restart")
    sys.exit(99)


def get_safe_param(jobj,pname):
    if pname in jobj:
        return jobj[pname]
    else:
        return None


def on_notice(raw_body):
    #print("Got notice", raw_body)
    try:
        task_spec = json.loads(raw_body.decode("utf-8"))
        cmd = task_spec["cmd"]
    except:
        logger.error("Invalid notice json: %r", raw_body)
        return

    if cmd == "exit":
        logger.info("Got exit command from RabbitMQ channel")
        helper.rabbit.stop()
    elif cmd == "update":
        update_self_then_restart()
    elif cmd == "ping":
        logger.info("Got ping command: " + get_safe_param(task_spec, "param"))
        helper.eventlog.info("PONG " + get_safe_param(task_spec, "param"))
    else:
        logger.error("Unknown notice cmd: %s", cmd)



def on_task(raw_body):
    #print("Got task", raw_body)
    try:
        task_spec = json.loads(raw_body.decode("utf-8"))
        cmd = task_spec["cmd"]
        ver = int(task_spec["ver"])
    except:
        logger.error("Invalid task json: %r", raw_body)
        return

    try:
        if cmd == "basic":
            handler_basic.process_basic_measurements(ver, task_spec)
        elif cmd == "score":
            handler_score.process_score_all(ver, task_spec)
        elif cmd == "byline":
            handler_byline.process_byline_extract(ver, task_spec)   # 이제 안씀
        elif cmd == "lab_split":
            handler_lab.process_split(ver, task_spec)
        elif cmd == "lab_postag":
            handler_lab.process_postag(ver, task_spec)
        elif cmd == "lab_sanitize":
            handler_lab.process_sanitize(ver, task_spec)
        elif cmd == "lab_metric":
            handler_lab.process_metric(ver, task_spec)
        elif cmd == "lab_trust":
            handler_lab.process_trust(ver, task_spec)
        elif cmd == "lab_integrate":
            handler_lab.process_integrate(ver, task_spec)
        else:
            logger.error("Unknown task cmd: %s", cmd)
            helper.eventlog.error("Unknown task cmd: %s" % cmd)

    except Exception as ex:
        newsId = task_spec["newsId"] if "newsId" in task_spec else "NoNews"
        #ex_type, ex_value, ex_traceback = sys.exc_info()
        #print("에러(%s,%s): %s,%s" % (cmd, newsId, ex_value.filename, ex_value.strerror))
        helper.eventlog.fatal("에러(%s,%s): %s" % (cmd, newsId, str(ex)))



helper.eventlog.set_worker_id(WORKER_ID)
if WORKER_ID != "dev":
    helper.eventlog.trace("Worker %s started (%d)" % (WORKER_ID, APP_VERSION))

logger.debug("Worker [%s] started (%d, %s)", WORKER_ID, APP_VERSION, os.environ["MQ_URL"])

# if __name__ == '__main__':
    # handler_basic.process_basic_measurements(1, {"newsId":"02100101.20160630120514682"})
    # handler_score.process_score_all(1, {"newsId":"02100101.20160630120514682"})
    # on_task({"cmd":"basic", "ver":"1", "newsId":"01101001.20160601133622578"})

# 변경한 가중치 적용 -> 기사평가(asStats)
#     coll_stat = helper.mongo.get_collection("asStats")
    # docs = coll_stat.find({})
    # for doc in docs:
    #     handler_score.process_score_all(1, {"newsId":doc["news_id"]})
    #     #print(doc["news_id"], doc["title"])

# 변경한 가중치 적용 -> 처리기사(news)
#     coll_news = helper.mongo.get_collection("news")
#     docs = coll_news.find({})
#     for doc in docs:
#         handler_basic.process_basic_measurements(1, {"newsId":doc["newsId"]})
        # print(doc["newsId"], doc["title"])

try:
    helper.rabbit.set_notice_handler(on_notice)
    helper.rabbit.set_task_handler(on_task)
    helper.rabbit.run(os.environ["MQ_URL"])
except KeyboardInterrupt:
    helper.rabbit.stop()

logger.debug("Worker [%s] stopped.", WORKER_ID)
