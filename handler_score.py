import datetime
import configparser
import helper.mongo

from ntrust import jnscore

def process_score_all(ver, param):
    news_id = param["newsId"]
    coll = helper.mongo.get_collection("news")
    coll_stat = helper.mongo.get_collection("asStats")

    doc = coll.find_one({"newsId":news_id})
    if not doc:
        raise RuntimeError("NotFound by newsId:" + news_id)

    category = doc["categoryFinal"]
    mediaType = "방송" if doc["mediaName"] in jnscore.BROADCASTS else "신문"
    jsco = jnscore.evaluate(category, mediaType, doc)

    coll.update_one({"newsId": news_id}, {"$set":{"score":jsco.scores}, "$unset":{"score_byline":""}}, upsert=False)
    #print(score_sets)

    coll_stat.update_one({"news_id": news_id}, {"$set":{"title": doc["title"], "score_totalSum": jsco.scores["totalSum"],
        "insertDt":doc["insertDt"],
        "journal": jsco.journal, "journal_totalSum": jsco.journalSum,
        "vanilla": jsco.vanilla, "vanilla_totalSum": jsco.vanillaSum
        }, "$unset":{"pubDate":""}}, upsert=False)
    print("Score updated: %s => %s" % (doc["title"], jsco.journalSum))



if __name__ == "__main__":
    print("yes, main")
    helper.mongo.connect()
    process_score_all(0, {"newsId":"01100101.20160601061030422"})