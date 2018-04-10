#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import helper.mongo

CATEGORIES = { "문화 예술", "국제", "연예", "라이프스타일", "사회", "정치", "IT 과학", "스포츠", "교육", "경제", "사설·칼럼" }
MEDIATYPES = { "신문", "방송" }
AGGR_PROPERTIES = { "contentLength", "quotes", "titleLength", "titleNumPuncs", "numNumber", "imageCount",
                    "avgSentenceLength", "numAnonPredicate", "numForeignWord", "titleAdverbs",
                    "avgAdverbsPerSentence", "quotePercent", "informantReal", "quoteRatioRealAnon" }

BROADCASTS = { "SBS", "MBC", "YTN" }

DOCKEY_CONTENT_LENGTH = "content_length"
DOCKEY_BYLINES = "bylines"
DOCKEY_QUOTES = "quotes"
DOCKEY_TITLE = "title"
DOCKEY_TITLE_NUM_EXCLAMATION = "title_numExclamation"
DOCKEY_TITLE_NUM_QUESTION = "title_numQuestion"
DOCKEY_CONTENT_NUM_NUMBER = "content_numNumber"
DOCKEY_IMAGE_COUNT = "image_count"
DOCKEY_CONTENT_AVG_SENTENCE_LENGTH = "content_avgSentenceLength"
DOCKEY_TITLE_ADVERBS = "title_adverbs"
DOCKEY_CONTENT_AVG_ADVERBS_PER_SENTENCE = "content_avgAdverbsPerSentence"
DOCKEY_CONTENT_QUOTE_PERCENT = "content_quotePercent"

class StatInfo:
    def __init__(self, item):
        #print(item)
        self.avg = item["avg"]
        self.min = item["min"]
        self.max = item["max"]
        self.sd = item["sd"]


class AggrStats:
    def load_data(self):
        self.data = dict()
        coll = helper.mongo.get_collection("newsAggr")
        docs = coll.find()
        for doc in docs:
            if doc["category"] not in CATEGORIES:
                raise RuntimeError("AggrStats: Unknown category: " + doc["category"])
            if doc["mediaType"] not in MEDIATYPES:
                raise RuntimeError("AggrStats: Unknown mediaType: " + doc["mediaType"])

            cate = doc["category"]
            mtype = doc["mediaType"]
            if cate not in self.data:
                self.data[cate] = dict()
            if mtype not in self.data[cate]:
                self.data[cate][mtype] = dict()

            for key in doc.keys():
                if key in [ "_id", "category", "mediaType", "count", "byline" ]:
                    continue
                if key not in AGGR_PROPERTIES:
                    raise RuntimeError("Unknown aggr property: " + key)
                self.data[cate][mtype][key] = StatInfo(doc[key])


    def get_stat(self, category, mediaType, property):
        return self.data[category][mediaType][property]


aggrStats = None

class JournalismScore:
    def __init__(self):
        self.scores = None
        self.journal = None
        self.journalSum = None
        self.vanilla = None
        self.vanillaSum = None

def evaluate(category, mediaType, doc):
    global aggrStats
    if not aggrStats:
        #raise RuntimeError("AggrStats not loaded")
        aggrStats = AggrStats()
        aggrStats.load_data()

    # 바이라인
    has_email = False
    has_name = False
    if "bylines" in doc:
        for bl in doc[DOCKEY_BYLINES]:
            if "name" in bl:
                has_name = True
            if "email" in bl:
                has_email = True

    score_byline = 0
    if has_name:
        if has_email:
            score_byline = 1  # 실명+이메일
        else:
            score_byline = 0.8  # 이름만 있음
    elif has_email:
        score_byline = 0  # 뭐 하나라도 있음
    else:
        score_byline = -1  # 둘다 없음

    # 기사 길이
    stat = aggrStats.get_stat(category, mediaType, "contentLength")
    contentLength = doc[DOCKEY_CONTENT_LENGTH]
    if contentLength <= (stat.avg):
        score_contentLength = 0
    if contentLength <= (stat.avg + 0.5 * stat.sd):
        score_contentLength = 0.165
    elif contentLength <= (stat.avg + stat.sd):
        score_contentLength = 0.33
    elif contentLength <= (stat.avg + 1.5 * stat.sd):
        score_contentLength = 0.495
    elif contentLength <= (stat.avg + 2.0 * stat.sd):
        score_contentLength = 0.66
    elif contentLength <= (stat.avg + 2.5 * stat.sd):
        score_contentLength = 0.835
    else:
        score_contentLength = 1

    # 인용문 수
    stat = aggrStats.get_stat(category, mediaType, "quotes")
    numQuotes = len(doc[DOCKEY_QUOTES])
    if numQuotes < 15:
        score_quoteCount = numQuotes / 15
    else:
        score_quoteCount = 1

    # 제목 길이
    stat = aggrStats.get_stat(category, mediaType, "titleLength")
    lenTitle = len(doc[DOCKEY_TITLE])
    if lenTitle <= 45:
        score_titleLength = 0
    else:
        score_titleLength = -1

    # 제목에 물음표/느낌표
    stat = aggrStats.get_stat(category, mediaType, "titleNumPuncs")
    numTitlePuncs = doc[DOCKEY_TITLE_NUM_EXCLAMATION] + doc[DOCKEY_TITLE_NUM_QUESTION]
    if numTitlePuncs == 0:
        score_titlePuncCount = 0
    elif numTitlePuncs == 1:
        score_titlePuncCount = -0.5
    else:
        score_titlePuncCount = -1

    # 수치 인용
    stat = aggrStats.get_stat(category, mediaType, "numNumber")
    numNumbers = doc[DOCKEY_CONTENT_NUM_NUMBER]
    if numNumbers < stat.avg:
        score_numberCount = 0
    elif numNumbers < (stat.avg + 0.5 * stat.sd):
        score_numberCount = 0.33
    elif numNumbers < (stat.avg + stat.sd):
        score_numberCount = 0.66
    else:
        score_numberCount = 1

    # 이미지 갯수
    stat = aggrStats.get_stat(category, mediaType, "imageCount")
    imageCount = doc[DOCKEY_IMAGE_COUNT]
    if imageCount <= 0:
        score_imageCount = 0
    elif imageCount == 1:
        score_imageCount = 0.33
    elif imageCount == 2:
        score_imageCount = 0.66
    elif imageCount == 3:
        score_imageCount = 1
    elif imageCount == 4:
        score_imageCount = 0.66
    elif imageCount == 5:
        score_imageCount = 0.33
    else: #imageCount >= 6:
        score_imageCount = 0

    # 평균 문장 길이
    stat = aggrStats.get_stat(category, mediaType, "avgSentenceLength")
    avgSentenceLength = doc[DOCKEY_CONTENT_AVG_SENTENCE_LENGTH]
    if avgSentenceLength >= (stat.avg + stat.sd):
        score_avgSentenceLength = -1
    else:
        score_avgSentenceLength = 0

    # 제목의 부사수
    stat = aggrStats.get_stat(category, mediaType, "titleAdverbs")
    numTitleAdverbs = len(doc[DOCKEY_TITLE_ADVERBS])
    if numTitleAdverbs == 1:
        score_titleAdverbCount = -0.5
    elif numTitleAdverbs >= 2:
        score_titleAdverbCount = -1
    else:
        score_titleAdverbCount = 0

    # 문장당 평균 부사수
    stat = aggrStats.get_stat(category, mediaType, "avgAdverbsPerSentence")
    avgAdverbsPerSentence = doc[DOCKEY_CONTENT_AVG_ADVERBS_PER_SENTENCE]
    if avgAdverbsPerSentence >= (stat.avg + 2 * stat.sd):
        score_avgAdverbCountPerSentence = -1
    else:
        score_avgAdverbCountPerSentence = 0

    # 인용문 길이 비율
    stat = aggrStats.get_stat(category, mediaType, "quotePercent")
    quotePercent = doc[DOCKEY_CONTENT_QUOTE_PERCENT]
    if quotePercent < 0.5:
        score_quotePercent = 0
    elif quotePercent < 0.8:
        score_quotePercent = -0.5
    else:
        score_quotePercent = -1

    # 아직 안되는 것들
    stat = aggrStats.get_stat(category, mediaType, "numAnonPredicate")
    score_anonPredicateCount = 0

    stat = aggrStats.get_stat(category, mediaType, "numForeignWord")
    score_foreignWordCount = 0

    stat = aggrStats.get_stat(category, mediaType, "informantReal")
    score_informantRealCount = 0

    stat = aggrStats.get_stat(category, mediaType, "quoteRatioRealAnon")
    score_quoteRatioRealAnon = 0


    ret = JournalismScore()

    score_totalSum = score_byline + score_contentLength + score_quoteCount + score_titleLength + score_titlePuncCount \
                     + score_numberCount + score_imageCount + score_avgSentenceLength + score_titleAdverbCount \
                     + score_avgAdverbCountPerSentence + score_quotePercent + score_anonPredicateCount \
                     + score_foreignWordCount + score_informantRealCount + score_quoteRatioRealAnon
    score_average = score_totalSum / 15

    ret.scores = { "totalSum": score_totalSum,
                   "average": score_average,
                   "byline": score_byline,
                   "contentLength": score_contentLength,
                   "quoteCount": score_quoteCount,
                   "titleLength": score_titleLength,
                   "titlePuncCount": score_titlePuncCount,
                   "numberCount": score_numberCount,
                   "imageCount": score_imageCount,
                   "avgSentenceLength": score_avgSentenceLength,
                   "titleAdverbCount": score_titleAdverbCount,
                   "avgAdverbCountPerSentence": score_avgAdverbCountPerSentence,
                   "quotePercent": score_quotePercent,
                   "anonPredicateCount": score_anonPredicateCount,
                   "foreignWordCount": score_foreignWordCount,
                   "informantRealCount": score_informantRealCount,
                   "quoteRatioRealAnon": score_quoteRatioRealAnon }

    # 독이성
    journal_read = score_byline * 0.001 \
                   + score_contentLength * 0.003 \
                   + score_quoteCount * 0.001 \
                   + score_titleLength * 1 \
                   + score_titlePuncCount * 1.002 \
                   + score_numberCount * 1.354 \
                   + score_imageCount * 1.5 \
                   + score_avgSentenceLength * 1.5 \
                   + score_titleAdverbCount * 2.466 \
                   + score_avgAdverbCountPerSentence * 0.5
    # 투명성
    journal_clear = score_byline * 4.498 \
                    + score_contentLength * 3.003 \
                    + score_quoteCount * 4.5 \
                    + score_titlePuncCount * 3.619 \
                    + score_numberCount * 1.454 \
                    + score_imageCount * 1 \
                    + score_quotePercent * 0.001
    # 사실성
    journal_truth = score_byline * 4.493 \
                    + score_contentLength * 3.503 \
                    + score_quoteCount * 3.501 \
                    + score_titlePuncCount * 0.001 \
                    + score_numberCount * 0.502 \
                    + score_imageCount * 1.5 \
                    + score_titleAdverbCount * 0.5 \
                    + score_avgAdverbCountPerSentence * 1.5 \
                    + score_quotePercent * 1
    # 유용성
    journal_useful = score_byline * 3.494 \
                     + score_contentLength * 3.498 \
                     + score_quoteCount * 2.001 \
                     + score_numberCount * 1.956 \
                     + score_imageCount * 1
    # 균형성
    journal_balance = score_byline * 2.996 \
                      + score_contentLength * 3.002 \
                      + score_quoteCount * 3 \
                      + score_titlePuncCount * 1.501 \
                      + score_titleAdverbCount * 0.501 \
                      + score_avgAdverbCountPerSentence * 1 \
                      + score_quotePercent * 1 \
    # 다양성
    journal_variety = score_byline * 0.998 \
                      + score_contentLength * 4.994 \
                      + score_quoteCount * 2.501 \
                      + score_titleLength * 0.5 \
                      + score_numberCount * 1.953 \
                      + score_imageCount * 1 \
                      + score_avgSentenceLength * 0.5 \
                      + score_quotePercent * 0.5
    # 독창성
    journal_original = score_byline * 4.494 \
                       + score_contentLength * 4.492 \
                       + score_quoteCount * 3.501 \
                       + score_titlePuncCount * 3.09 \
                       + score_numberCount * 1.823 \
                       + score_imageCount * 1.501
    # 중요성
    journal_important = score_byline * 2.495 \
                        + score_contentLength * 3.503 \
                        + score_quoteCount * 3.5 \
                        + score_numberCount * 1.002 \
                        + score_imageCount * 0.5
    # 심층성
    journal_deep = score_byline * 4.496 \
                   + score_contentLength * 4.995 \
                   + score_quoteCount * 3.501 \
                   + score_numberCount * 1.336 \
                   + score_imageCount * 1 \
                   + score_quotePercent * 1
    # 선정성
    journal_yellow = score_byline * 4.491 \
                     + score_titleLength * 3.5 \
                     + score_titlePuncCount * 3.501 \
                     + score_titleAdverbCount * 3.5 \
                     + score_avgAdverbCountPerSentence * 3.5 \
                     + score_quotePercent * 3.5

    ret.journalSum = journal_read + journal_clear + journal_truth + journal_useful + journal_balance \
                     + journal_variety + journal_original + journal_important + journal_deep + journal_yellow

    ret.journal = { "readability": journal_read,
                     "transparency": journal_clear,
                     "factuality": journal_truth,
                     "utility": journal_useful,
                     "fairness": journal_balance,
                     "diversity": journal_variety,
                     "originality": journal_original,
                     "importance": journal_important,
                     "depth": journal_deep,
                     "sensationalism": journal_yellow }


    # 독이성
    vanilla_read = score_byline \
                   + score_contentLength \
                   + score_quoteCount \
                   + score_titleLength \
                   + score_titlePuncCount \
                   + score_numberCount \
                   + score_imageCount \
                   + score_avgSentenceLength \
                   + score_titleAdverbCount \
                   + score_avgAdverbCountPerSentence
    # 투명성
    vanilla_clear = score_byline \
                    + score_contentLength \
                    + score_quoteCount \
                    + score_titlePuncCount \
                    + score_numberCount \
                    + score_imageCount \
                    + score_quotePercent
    # 사실성
    vanilla_truth = score_byline \
                    + score_contentLength \
                    + score_quoteCount \
                    + score_titlePuncCount \
                    + score_numberCount \
                    + score_imageCount \
                    + score_titleAdverbCount \
                    + score_avgAdverbCountPerSentence \
                    + score_quotePercent
    # 유용성
    vanilla_useful = score_byline \
                     + score_contentLength \
                     + score_quoteCount \
                     + score_numberCount \
                     + score_imageCount
    # 균형성
    vanilla_balance = score_byline \
                      + score_contentLength \
                      + score_quoteCount \
                      + score_titlePuncCount \
                      + score_titleAdverbCount \
                      + score_avgAdverbCountPerSentence \
                      + score_quotePercent
    # 다양성
    vanilla_variety = score_byline \
                      + score_contentLength \
                      + score_quoteCount \
                      + score_titleLength \
                      + score_numberCount \
                      + score_imageCount \
                      + score_avgSentenceLength \
                      + score_quotePercent
    # 독창성
    vanilla_original = score_byline \
                       + score_contentLength \
                       + score_quoteCount \
                       + score_titlePuncCount \
                       + score_numberCount \
                       + score_imageCount
    # 중요성
    vanilla_important = score_byline \
                        + score_contentLength \
                        + score_quoteCount \
                        + score_numberCount \
                        + score_imageCount
    # 심층성
    vanilla_deep = score_byline \
                   + score_contentLength \
                   + score_quoteCount \
                   + score_numberCount \
                   + score_imageCount \
                   + score_quotePercent
    # 선정성
    vanilla_yellow = score_byline \
                     + score_titleLength \
                     + score_titlePuncCount \
                     + score_titleAdverbCount \
                     + score_avgAdverbCountPerSentence \
                     + score_quotePercent

    ret.vanillaSum = vanilla_read + vanilla_clear + vanilla_truth + vanilla_useful + vanilla_balance \
                       + vanilla_variety + vanilla_original + vanilla_important + vanilla_deep + vanilla_yellow

    ret.vanilla = { "readability": vanilla_read,
                     "transparency": vanilla_clear,
                     "factuality": vanilla_truth,
                     "utility": vanilla_useful,
                     "fairness": vanilla_balance,
                     "diversity": vanilla_variety,
                     "originality": vanilla_original,
                     "importance": vanilla_important,
                     "depth": vanilla_deep,
                     "sensationalism": vanilla_yellow }

    return ret