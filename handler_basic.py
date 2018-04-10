import datetime
import timeit

from konlpy.tag import Hannanum
from konlpy.tag import Kkma
from konlpy.tag import Komoran
from konlpy.tag import Twitter
from bson.objectid import ObjectId

import helper
from ntrust import tagger
from ntrust import textcount
from ntrust import sentences
from ntrust import jnscore
from ntrust import anonpred

import ntrust.content
import ntrust.byline

COLLNAME_CM_NEWS = "cm2016"
COLLNAME_NEWS = "news"
COLLNAME_NEWS_ENTITY = "news_entity"



hannanum = Hannanum()
kkma = Kkma()
komoran = Komoran()
twitter = Twitter()

def get_metric_update_dicts(params):
    import helper.entity_coll

    title = params["title"]
    content = params["content"]

    media_id = params["mediaId"] if "mediaId" in params else None
    image_count = params["imageCount"] if "imageCount" in params else 0

    main_sets = dict()
    main_unsets = dict()

    # title
    #main_sets["title"] = title
    main_sets["title_length"] = textcount.length(title)
    main_sets[jnscore.DOCKEY_TITLE_NUM_EXCLAMATION] = textcount.number_of_exclamation_marks(title)
    main_sets[jnscore.DOCKEY_TITLE_NUM_QUESTION] = textcount.number_of_question_marks(title)
    main_sets["title_numPuncs"] = main_sets["title_numExclamation"] + main_sets["title_numQuestion"]
    main_sets["title_numSingleQuote"] = textcount.number_of_singlequote_marks(title)
    main_sets["title_numDoubleQuote"] = textcount.number_of_doublequote_marks(title)
    main_sets["title_hasShock"] = textcount.is_title_shock_ohmy(title)
    main_sets["title_hasExclusive"] = textcount.is_title_exclusive_news(title)
    main_sets["title_hasBreaking"] = textcount.is_title_breaking_news(title)
    main_sets["title_hasPlan"] = textcount.is_title_plan_news(title)

    # image
    main_sets[jnscore.DOCKEY_IMAGE_COUNT] = image_count

    # content
    san = ntrust.content.Sanitizer(media_id)
    san.process(content)
    sancon = san.get_contents()
    main_sets["content"] = sancon
    content_length = textcount.length(sancon)
    main_sets[jnscore.DOCKEY_CONTENT_LENGTH] = content_length

    # 본문에서 바이라인 추출
    bylines = san.get_bylines()
    if bylines:
        main_sets[jnscore.DOCKEY_BYLINES] = bylines
    else:
        main_unsets[jnscore.DOCKEY_BYLINES] = 1

    # 인용문 추출
    quotes = sentences.extract_quoted(sancon)
    qarr = list()
    total_quotes_len = 0
    if quotes:
        for qs in quotes:
            if textcount.number_of_white_spaces(qs) >= 2:
                qlen = textcount.length(qs)
                total_quotes_len += qlen
                qarr.append({"sentence":qs, "length":qlen})
    main_sets[jnscore.DOCKEY_QUOTES] = qarr  # 빈 qarr 도 저장하라고 해서..
    main_sets[jnscore.DOCKEY_CONTENT_QUOTE_PERCENT] = (total_quotes_len / content_length) if content_length > 0 else 0

    # 형태소 분석 및 인용문 앞부분 추출에 사용
    lines = sancon.split("\n")


    # 문장 갯수
    num_sentence = len(lines)
    main_sets["content_numSentence"] = num_sentence

    # 문장 당 평균 길이
    avgSentenceLength = 0
    if num_sentence > 0:
        sumSentenceLength = 0
        for line in lines:
            sumSentenceLength += len(line)
        avgSentenceLength = float(sumSentenceLength) / num_sentence

    main_sets[jnscore.DOCKEY_CONTENT_AVG_SENTENCE_LENGTH] = avgSentenceLength


    # 인용문 앞부분 추출
    if quotes:
        for line in lines:
            for qdic in main_sets[jnscore.DOCKEY_QUOTES]:
                if "frontText" not in qdic and line.find(qdic["sentence"]) >= 0:
                    qdic["frontText"] = sentences.get_text_front_quote(line, qdic["sentence"])


    # 형태소 분석
    news_entity = dict()
    num_adverbs = 0
    num_adjectives = 0
    num_conjunctions = 0

    # Mecab
    mecab_tags = []
    mecab_start_time = timeit.default_timer()
    for line in lines:
        tagResults = tagger.merge(line, deep=False)
        for tres in tagResults:
            # print(tres)
            if tres[0] == "":
                continue

            if '-' not in tres[2]:
                pos = ','.join(tres[1])
                mecab_tags.append({"word": tres[0], "pos": pos})

    mecab_end_time = timeit.default_timer()
    news_entity["mecab_time"] = mecab_end_time - mecab_start_time
    news_entity["mecab_postag"] = mecab_tags
    # print("Mecab: %f seconds: %s" % (update_set["mecab_time"], update_set["mecab_postag"]))

    ec_mecab = helper.entity_coll.EntityCollector()
    for item in mecab_tags:
        for pos in item["pos"].split(","):
            if pos.startswith('N'):
                ec_mecab.feed(item["word"])

            if pos.startswith("MAG"):
                num_adverbs += 1
            elif pos.startswith("MAJ"):
                num_conjunctions += 1
            elif pos.startswith("VA"):
                num_adjectives += 1

    ec_mecab.get_result("mecab_", news_entity)

    # Hannanum
    hannn_tags = []
    hannn_start_time = timeit.default_timer()
    for line in lines:
        hpos = hannanum.pos(line)
        for pos in hpos:
            hannn_tags.append({"word": pos[0], "pos": pos[1]})

    hannn_end_time = timeit.default_timer()
    news_entity["hannanum_time"] = hannn_end_time - hannn_start_time
    news_entity["hannanum_postag"] = hannn_tags
    # print("Hannanum: %f seconds: %s" % (update_set["hannanum_time"], update_set["hannanum_postag"]))

    ec_hannanum = helper.entity_coll.EntityCollector()
    for item in hannn_tags:
        if item["pos"].startswith('N'):
            ec_hannanum.feed(item["word"])
    ec_hannanum.get_result("hannanum_", news_entity)

    # Kkma
    kkma_tags = []
    kkma_start_time = timeit.default_timer()
    for line in lines:
        kpos = kkma.pos(line)
        for pos in kpos:
            kkma_tags.append({"word": pos[0], "pos": pos[1]})

    kkma_end_time = timeit.default_timer()
    news_entity["kkma_time"] = kkma_end_time - kkma_start_time
    news_entity["kkma_postag"] = kkma_tags
    # print("Kkma: %f seconds: %s" % (update_set["kkma_time"], update_set["kkma_postag"]))

    ec_kkma = helper.entity_coll.EntityCollector()
    for item in kkma_tags:
        if item["pos"].startswith('N'):
            ec_kkma.feed(item["word"])
    ec_kkma.get_result("kkma_", news_entity)

    # Twitter
    twit_tags = []
    twit_start_time = timeit.default_timer()
    for line in lines:
        tpos = twitter.pos(line)
        for pos in tpos:
            twit_tags.append({"word": pos[0], "pos": pos[1]})

    twit_end_time = timeit.default_timer()
    news_entity["twitter_time"] = twit_end_time - twit_start_time
    news_entity["twitter_postag"] = twit_tags
    # print("Twitter: %f seconds: %s" % (update_set["twitter_time"], update_set["twitter_postag"]))

    ec_twit = helper.entity_coll.EntityCollector()
    for item in twit_tags:
        if item["pos"].startswith('N'):
            ec_twit.feed(item["word"])
    ec_twit.get_result("twitter_", news_entity)


    # 문장 당 평균 부사 수
    main_sets["content_numAdverb"] = num_adverbs
    main_sets["content_numAdjective"] = num_adjectives
    main_sets["content_numConjunction"] = num_conjunctions
    main_sets["content_avgAdverbsPerSentence"] = (num_adverbs / num_sentence) if num_sentence > 0 else 0

    # 본문에 수치 인용 개수
    num_numbers = 0
    postags = news_entity["mecab_postag"]
    for item in postags:
        if item["pos"].startswith('SN'):
            num_numbers += 1

    main_sets[jnscore.DOCKEY_CONTENT_NUM_NUMBER] = num_numbers

    main_sets["content_anonPredicates"] = anonpred.find_anonymous_predicates(sancon)

    # TODO
    #main_sets["content_numForeignWord"] = 0
    main_sets["informant_real"] = []
    main_sets["quotes_ratioRealAnon"] = 0

    # 제목에 부사 수
    title_adverbs = []
    titlePos = kkma.pos(title)
    for pos in titlePos:
        if pos[1] == "MAG":
            title_adverbs.append(pos[0])

    main_sets["title_adverbs"] = title_adverbs

    return ({"$set":main_sets, "$unset":main_unsets}, news_entity)





def process_basic_measurements(ver, param):
    news_id = param["newsId"]

    coll_src = helper.mongo.get_collection(COLLNAME_CM_NEWS)
    coll_dst = helper.mongo.get_collection(COLLNAME_NEWS)
    coll_ett = helper.mongo.get_collection(COLLNAME_NEWS_ENTITY)

    print("Begin %s" % (news_id))

    src = coll_src.find_one({"newsitem_id":news_id})
    if src is None:
        helper.eventlog.error("Source news item not found: %s" % news_id)
        return

    chgs_news, chgs_entity = get_metric_update_dicts({
        "mediaId": src['media_id'],
        "title": src["title"],
        "content": src["news_content"],
        "imageCount":src["news_img_cnt"]
    })

    main_sets = chgs_news["$set"]
    main_sets["runSpec"] = 3
    main_sets["runDate"] = datetime.datetime.utcnow()

    writer_byline = src["writer_byline"]
    writer_email = src["writer_email"]
    writer_post = src["writer_post"]

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

        main_sets["byline_writer"] = wr

        # 경향신문은 바이라인이 본문에 없고 byline_writer 에 값이 있는 경우가 다수 발견,
        # main_sets["bylines"] 가 비었을 경우 byline_writer 를 넣도록 한다.
        if "bylines" not in main_sets and len(wr) > 0:
            main_sets["bylines"] = [wr]
            chgs_news["$unset"].pop("bylines",None)
    else:
        chgs_news["$unset"]["byline_writer"] = 1


    if len(chgs_news["$unset"]) == 0:
        chgs_news.pop("$unset")

    coll_dst.update_one({"newsId": news_id}, chgs_news, upsert=False)

    chgs_entity["newsId"] = news_id;
    coll_ett.replace_one({"newsId": news_id}, chgs_entity)



    # 2017.12.12 기사평가로직 추가
    doc = coll_dst.find_one({"newsId":news_id})
    category = doc["categoryFinal"]
    mediaType = "방송" if doc["mediaName"] in jnscore.BROADCASTS else "신문"
    jsco = jnscore.evaluate(category, mediaType, doc)

    coll_dst.update_one({"newsId": news_id}, {"$set":{
        "journal":jsco.journal,
        "journal_totalSum": jsco.journalSum,
        "vanilla": jsco.vanilla,
        "vanilla_totalSum": jsco.vanillaSum,
        "score": jsco.scores
    }}, upsert=False)

    print("  Done %s: %s" % (news_id, src["title"]))



if __name__ == "__main__":
    print("Do not execute this script standalone.")