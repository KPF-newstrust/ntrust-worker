import datetime
import timeit

from konlpy.tag import Hannanum
from konlpy.tag import Kkma
from konlpy.tag import Komoran
from konlpy.tag import Twitter
from bson.objectid import ObjectId

import helper
import ntrust
from ntrust import tagger
from ntrust import textcount
from ntrust import sentences
from ntrust import jnscore

COLLNAME_APILAB = "apilab"

def _lab_common(param, core_method):
    coll_apilab = helper.mongo.get_collection(COLLNAME_APILAB)

    obj_id = ObjectId(param["id"])
    doc = coll_apilab.find_one({"_id":obj_id})
    if doc is None:
        helper.eventlog.error("ApiLab item not found: %s" % obj_id)
        return

    update_set = core_method(doc)

    if update_set:
        update_set["completedAt"] = datetime.datetime.utcnow()
        coll_apilab.update_one({"_id": obj_id}, {"$set": update_set}, upsert=False)
        #print("\nLabItem done:", obj_id)





hannanum = Hannanum()
kkma = Kkma()
komoran = Komoran()
twitter = Twitter()

def _lab_process(param, **kwargs):
    coll_apilab = helper.mongo.get_collection(COLLNAME_APILAB)

    obj_id = ObjectId(param["id"])
    doc = coll_apilab.find_one({"_id":obj_id})
    if doc is None:
        helper.eventlog.error("ApiLab item not found: %s" % obj_id)
        return

    title = doc['title']
    content = doc['content']

    update_set = dict()

    if "split" in kwargs:
        lines = list(ntrust.sentences.split_sentence(content))
        num_sentence = len(lines)
        content = update_set["result"] = "\n".join(lines)


    if "sanitize" in kwargs:
        san = ntrust.content.Sanitizer("labtest")
        san.process(content)
        content = update_set["result"] = san.get_contents()
        num_sentence = len(san.get_contents_lines())
        bylines = san.get_bylines()
        if bylines:
            update_set[jnscore.DOCKEY_BYLINES] = bylines


    if "postag" in kwargs:
        lines = content.split("\n")
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
        update_set["mecab_time"] = mecab_end_time - mecab_start_time
        update_set["mecab_postag"] = mecab_tags
        # print("Mecab: %f seconds: %s" % (update_set["mecab_time"], update_set["mecab_postag"]))

        # Hannanum
        hannn_tags = []
        hannn_start_time = timeit.default_timer()
        for line in lines:
            hpos = hannanum.pos(line)
            for pos in hpos:
                hannn_tags.append({"word": pos[0], "pos": pos[1]})

        hannn_end_time = timeit.default_timer()
        update_set["hannanum_time"] = hannn_end_time - hannn_start_time
        update_set["hannanum_postag"] = hannn_tags
        # print("Hannanum: %f seconds: %s" % (update_set["hannanum_time"], update_set["hannanum_postag"]))

        # Kkma
        kkma_tags = []
        kkma_start_time = timeit.default_timer()
        for line in lines:
            kpos = kkma.pos(line)
            for pos in kpos:
                kkma_tags.append({"word": pos[0], "pos": pos[1]})

        kkma_end_time = timeit.default_timer()
        update_set["kkma_time"] = kkma_end_time - kkma_start_time
        update_set["kkma_postag"] = kkma_tags
        # print("Kkma: %f seconds: %s" % (update_set["kkma_time"], update_set["kkma_postag"]))

        # Twitter
        twit_tags = []
        twit_start_time = timeit.default_timer()
        for line in lines:
            tpos = twitter.pos(line)
            for pos in tpos:
                twit_tags.append({"word": pos[0], "pos": pos[1]})

        twit_end_time = timeit.default_timer()
        update_set["twitter_time"] = twit_end_time - twit_start_time
        update_set["twitter_postag"] = twit_tags
        # print("Twitter: %f seconds: %s" % (update_set["twitter_time"], update_set["twitter_postag"]))


    if "metric" in kwargs:
        content_length = textcount.length(content)
        update_set[jnscore.DOCKEY_CONTENT_LENGTH] = content_length
        update_set["title_length"] = textcount.length(title)
        update_set[jnscore.DOCKEY_TITLE_NUM_EXCLAMATION] = textcount.number_of_exclamation_marks(title)
        update_set[jnscore.DOCKEY_TITLE_NUM_QUESTION] = textcount.number_of_question_marks(title)
        update_set["title_numSingleQuote"] = textcount.number_of_singlequote_marks(title)
        update_set["title_numDoubleQuote"] = textcount.number_of_doublequote_marks(title)
        update_set["title_hasShock"] = textcount.is_title_shock_ohmy(title)
        update_set["title_hasExclusive"] = textcount.is_title_exclusive_news(title)
        update_set["title_hasBreaking"] = textcount.is_title_breaking_news(title)
        update_set["title_hasPlan"] = textcount.is_title_plan_news(title)

        total_quotes_len = 0
        quotes = sentences.extract_quoted(content)
        if quotes:
            qarr = list()
            for qs in quotes:
                if textcount.number_of_white_spaces(qs) >= 2:
                    qlen = textcount.length(qs)
                    total_quotes_len += qlen
                    qarr.append({"sentence": qs, "length": qlen})
            update_set[jnscore.DOCKEY_QUOTES] = qarr

        # 인용문 본문 비율
        update_set[jnscore.DOCKEY_CONTENT_QUOTE_PERCENT] = (total_quotes_len / content_length) if content_length > 0 else 0

        # 문장 갯수
        update_set["content_numSentence"] = num_sentence

        # 문장 당 평균 길이
        avgSentenceLength = 0
        if num_sentence > 0:
            sumSentenceLength = 0
            for line in content.split("\n"):
                sumSentenceLength += len(line)
            avgSentenceLength = float(sumSentenceLength) / num_sentence

        update_set[jnscore.DOCKEY_CONTENT_AVG_SENTENCE_LENGTH] = avgSentenceLength

        # 본문에 수치 인용 개수, 문장 당 평균 부사 수
        num_numbers = 0
        num_adverbs = 0
        num_adjectives = 0
        num_conjunctions = 0

        postags = update_set["mecab_postag"]
        for item in postags:
            if item["pos"].startswith('SN'):
                num_numbers += 1

            for pos in item["pos"].split(","):
                if pos.startswith('SN'):
                    num_numbers += 1
                if pos.startswith("MAG"):
                    num_adverbs += 1
                elif pos.startswith("MAJ"):
                    num_conjunctions += 1
                elif pos.startswith("VA"):
                    num_adjectives += 1

        update_set["content_numAdverb"] = num_adverbs
        update_set["content_numAdjective"] = num_adjectives
        update_set["content_numConjunction"] = num_conjunctions
        update_set[jnscore.DOCKEY_CONTENT_AVG_ADVERBS_PER_SENTENCE] = (num_adverbs / num_sentence) if num_sentence > 0 else 0
        update_set[jnscore.DOCKEY_CONTENT_NUM_NUMBER] = num_numbers

        # 제목에 부사 수
        title_adverbs = []
        titlePos = kkma.pos(title)
        for pos in titlePos:
            if pos[1] == "MAG":
                title_adverbs.append(pos[0])

        update_set[jnscore.DOCKEY_TITLE_ADVERBS] = title_adverbs

    if "trust" in kwargs:
        doc.update(update_set)
        doc[jnscore.DOCKEY_IMAGE_COUNT] = 0
        jsco = jnscore.evaluate(doc["category"],doc["mediaType"], doc)
        update_set["journal"] = jsco.journal
        update_set["journal_totalSum"] = jsco.journalSum
        update_set["vanilla"] = jsco.vanilla
        update_set["vanilla_totalSum"] = jsco.vanillaSum
        update_set["score"] = jsco.scores

    update_set["completedAt"] = datetime.datetime.utcnow()
    coll_apilab.update_one({"_id": obj_id}, {"$set": update_set}, upsert=False)
    print("\nLabItem done:", obj_id)

################################################################################

def process_split(ver, param):
    _lab_process(param, split=1)

def process_postag(ver, param):
    _lab_process(param, split=1, postag=1)

def process_sanitize(ver, param):
    _lab_process(param, sanitize=1)

def process_metric(ver, param):
    _lab_process(param, sanitize=1, postag=1, metric=1)

def process_trust(ver, param):
    _lab_process(param, sanitize=1, postag=1, metric=1, trust=1)

def process_integrate(ver, param):
    _lab_process(param, sanitize=1, postag=1, metric=1, trust=1)

################################################################################

if __name__ == "__main__":
    print("Do not execute this script standalone.")