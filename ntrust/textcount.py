import re
from . import util

RE_DOUBLE_SPACE = re.compile("(\s{2,})")
RE_QUESTION_MARK = re.compile("\?")
RE_EXCLAMATION_MARK = re.compile("!")
RE_SINGLEQUOTE_MARK = re.compile("'|‘|’")
RE_DOUBLEQUOTE_MARK = re.compile('"|“|”')
RE_SPACE_CHAR = re.compile(u'( |\t|\xa0|\xeb|\u3000|\u2028|\u2029)+')

RE_SHOCK_OHMY = re.compile("충격.+이럴")
RE_TITLE_EXCLUSIVE = re.compile("^.{0,3}단독")
RE_TITLE_BREAKING = re.compile("^.{0,3}속보")
RE_TITLE_PLAN = re.compile("^.{0,3}기획")

# 공백 연속을 한개로 카운팅
def length(txt):
    txt = util.clean_content(txt, True)
    if RE_DOUBLE_SPACE.search(txt):
        txt = RE_DOUBLE_SPACE.sub(' ', txt)
    return len(txt)

# 물음표 수
def number_of_question_marks(txt):
    return len(RE_QUESTION_MARK.findall(txt))

# 느낌표 수
def number_of_exclamation_marks(txt):
    return len(RE_EXCLAMATION_MARK.findall(txt))

# (제목내) 홑따옴표
def number_of_singlequote_marks(txt):
    cnt = len(RE_SINGLEQUOTE_MARK.findall(txt))
    return cnt

# (제목내) 겹따옴표 수
def number_of_doublequote_marks(txt):
    cnt = len(RE_DOUBLEQUOTE_MARK.findall(txt))
    return cnt

# 공백문자 수
def number_of_white_spaces(txt):
    cnt = len(RE_SPACE_CHAR.findall(txt))
    return cnt

def is_title_shock_ohmy(txt):
    return len(RE_SHOCK_OHMY.findall(txt)) > 0

def is_title_exclusive_news(txt):
    return len(RE_TITLE_EXCLUSIVE.findall(txt)) > 0

def is_title_breaking_news(txt):
    return len(RE_TITLE_BREAKING.findall(txt)) > 0

def is_title_plan_news(txt):
    return len(RE_TITLE_PLAN.findall(txt)) > 0
