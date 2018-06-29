import datetime

import helper
import ntrust.byline
import ntrust.content

COLLNAME_NEWS_SRC = "news_src"
COLLNAME_NEWS = "news"

def process_score_byline(ver, param):
    news_id = param["newsId"]

    coll_news = helper.mongo.get_collection(COLLNAME_NEWS)

    doc = coll_news.find_one({"newsId":news_id}, {"bylines":1})
    if doc is None:
        helper.eventlog.warning("Source news item not found: %s" % news_id)
        return

    has_email = False
    has_name = False
    if "bylines" in doc:
        for bl in doc["bylines"]:
            if "name" in bl:
                has_name = True
            if "email" in bl:
                has_email = True

    score = 0
    if has_name:
        if has_email:
            score = 1   # 실명+이메일
        else:
            score = 0.8 # 이름만 있음
    elif has_email:
        score = 0   # 뭐 하나라도 있음
    else:
        score = -1  # 둘다 없음

    coll_news.update_one({"newsId": news_id}, {"$set":{"score_byline":score}}, upsert=False)
    #print("\nUpdated %s: score_byline=%f" % (news_id, score))


def process_byline_extract(ver, param):
    news_id = param["newsId"]

    coll_src = helper.mongo.get_collection(COLLNAME_NEWS_SRC)
    coll_dst = helper.mongo.get_collection(COLLNAME_NEWS)

    doc = coll_src.find_one({"newsitem_id":news_id})
    if doc is None:
        #helper.eventlog.error("Source news item not found: %s" % news_id)
        return

    remove_set = dict()
    update_set = dict()
    update_set["runSpec"] = 3
    update_set["runDate"] = datetime.datetime.utcnow()

    san = ntrust.content.Sanitizer(doc['media_id'])
    san.process(doc["news_content"])
    update_set["content"] = san.get_contents()
    bylines = san.get_bylines()
    if bylines:
        #print("Extracted bylines:", bylines)
        update_set["bylines"] = bylines
    else:
        remove_set["bylines"] = 1

    writer_byline = doc["writer_byline"]
    writer_email = doc["writer_email"]
    writer_post = doc["writer_post"]

    if len(writer_byline) > 1:
        wr = dict();
        if len(writer_post) > 1:
            wr["post"] = writer_post
        if len(writer_email) > 1:
            wr["email"] = writer_email
        if ntrust.byline.find_likely_email(writer_byline):
            # 바이라인에 이메일이 포함되어 있는 경우가 있다.
            wbyline = ntrust.byline.BylineExtractor(writer_byline).get_result()
            if "name" in wbyline:
                wr["name"] = wbyline["name"]
            if "email" in wbyline:
                wr["email"] = wbyline["email"]
        else:
            wr["name"] = writer_byline

        update_set["byline_writer"] = wr

    upd_param = {"$set": update_set}
    if len(remove_set) > 0:
        upd_param["$unset"] = remove_set

    coll_dst.update_one({"newsId": news_id}, upd_param, upsert=False)
    print("\nUpdated byline_writer:", news_id)


if __name__ == "__main__":
    print("Do not execute this script standalone.")