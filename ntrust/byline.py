import logging
import re

RE_EMAIL = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+[a-zA-Z0-9-.]+')
RE_ALPHA_NUMERIC_IDENTIFIER = re.compile(r'[a-zA-Z0-9_.+-]+@?')
RE_JOURNALIST_JOB = re.compile(r'인턴기자|기자|특파원|논설위원|논설실장')
RE_TV_JOURNALIST = re.compile(r'(MBC|SBS|KBS|YTN).*?\s(.+)입')
RE_YTN_JOURNALIST = re.compile(r'YTN.*?\s(.+?)\[([a-zA-Z0-9-]*)')
RE_BYLINE_DIV_CHARS = re.compile(r'[·/|\[\]]')

# FIXME: 지역명은 따로 빼야 하는데.
RE_COMPANY_NAMES = re.compile(r'아시아투데이|한경닷컴|충청일보|중부매일|포항|디지털뉴스국')

S_PUNCTUATION_CHARS = """!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~‘’“”▶▷■▦△▲◇"""
S_WHITE_SPACES = " \t\xa0\xeb\u3000\u2028\u2029"

from .textcount import RE_SPACE_CHAR

# text 에서 꽤나 email 스러운 것을 찾아서 리턴합니다.
def find_likely_email(text):
    m = RE_EMAIL.search(text)
    return m.group(0) if m else None


# text 에서 알파벳과 숫자 _, . 등의 연속으로 이루어진 단어를 찾아 리턴합니다.
# 이메일 같이 생겼는데 @ 문자가 빠진 경우에 사용합니다. (아이디만 있는 경우)
def find_alpha_numeric(text):
    m = RE_ALPHA_NUMERIC_IDENTIFIER.search(text)
    return m.group(0) if m else None


# 바이라인 유추가 가능한 "기자", "특파원", "리포터" 등의 한글 직업명을 찾아서 리턴합니다.
def find_journalist_job(text):
    m = RE_JOURNALIST_JOB.search(text)
    return m.group(0) if m else None


# 주어진 텍스트가 바이라인일 가능성이 있나?
def can_be_byline(text):
    return True if find_likely_email(text) or find_journalist_job(text) else False


def split_get_left_right(long_text, split_word, nostrip=False):
    idx = long_text.rfind(split_word)
    if idx < 0:
        return (None,None)
    idx2 = idx + len(split_word)
    if nostrip:
        return (long_text[:idx], long_text[idx2:])
    return (long_text[:idx].strip(), long_text[idx2:].strip())



def head_to_tail_until_punctuation_char(text):
    if not text:
        return None
    for n, ch in enumerate(text):
        if ch in S_PUNCTUATION_CHARS:
            return text[:n].rstrip()
    return text.rstrip()


def tail_to_head_until_punctuation_char(text):
    if not text:
        return None
    for n, ch in enumerate(text[::-1]):
        if ch in S_PUNCTUATION_CHARS:
            return text[(len(text) - n):].lstrip()
    return text.lstrip()


# "홍길동기자" --> "홍길동 기자"
def normalize_name_with_job(namepart,jobname):
    if not namepart or not jobname:
        return None

    # 아시아투데이 박아람 기자 --> 박아람 기자
    company = RE_COMPANY_NAMES.search(namepart)
    if company:
        namepart = namepart.replace(company.group(0), '').strip()

    if len(namepart) > 0 and namepart[-1] in S_WHITE_SPACES:
        # 직업명 앞에 띄워쓰기가 있으므로 별도 처리가 필요 없다.
        namepart = namepart.strip()
        if not namepart:
            return None # 기자 앞에 이름이 없다.
        return (namepart + ' ' + jobname)

    num_spaces = len(RE_SPACE_CHAR.findall(namepart))
    if num_spaces > 0:
        # "홍길동 수습기자" 같은 경우 .. 새로운 직업명일 수 있다.
        return (namepart + jobname)

    # "홍길동기자" 같은 경우, 띄워쓰기를 넣어준다.
    return (namepart + ' ' + jobname)


class BylineExtractor(object):
    GENERAL = 1
    TV = 2

    def __init__(self, text, type=GENERAL):
        if type == BylineExtractor.TV:
            self.analyze_tv(text)
        else:
            self.analyze(text)


    def analyze(self, text):
        self.original_text = text
        self.components = dict()

        maybe_email = find_likely_email(text)
        if maybe_email:
            self.components["email"] = maybe_email
            left, right = split_get_left_right(text, maybe_email)

            maybe_job = find_journalist_job(left)
            if maybe_job:
                maybe_name = left
                redundant_job = find_journalist_job(right)
            else:
                redundant_job = None
                maybe_job = find_journalist_job(right)
                maybe_name = right if maybe_job else None


            if redundant_job:
                # TODO: log doubtful case
                logging.warning("redundant journalist job found in '%s'", text)

            if maybe_name:
                maybe_name, name_right = split_get_left_right(maybe_name, maybe_job, nostrip=True)
                maybe_name = tail_to_head_until_punctuation_char(maybe_name)
                name_right = head_to_tail_until_punctuation_char(name_right)
                name = normalize_name_with_job(maybe_name, maybe_job)
                if name:
                    # 기자 뒤 email 앞에 텍스트가 있을 경우 기자명에 포함시킴 (예: "증시분석 전문기자 로봇 ET")
                    if name_right and name_right.strip():
                        name = name + name_right
                    self.components["name"] = name
                    return

            # 이메일 앞에 보통 이름이 오는데 "기자" 직업명이 없다. 글자수가 4글자 이하면 이름으로 간주한다.
            name = tail_to_head_until_punctuation_char(left or right)
            if name:
                if len(name) <= 4:
                    self.components["name"] = name
                elif name[-1] == "팀":
                    # 혹시 ~팀 으로 끝나는 경우 이름으로 간주 (예: 산업경제팀)
                    self.components["name"] = name

            return

        # 이메일이 없는 경우 (예: "홍길동 기자" 또는 "홍길동 기자 hong")
        # 일단 기자 등의 직업명이 보여야 한다.
        maybe_job = find_journalist_job(text)
        if maybe_job:
            left, right = split_get_left_right(text, maybe_job, nostrip=True)
            maybe_name = tail_to_head_until_punctuation_char(left)
            name = normalize_name_with_job(maybe_name, maybe_job)
            if name:
                self.components["name"] = name
                maybe_email = find_alpha_numeric(right)
                if maybe_email:
                    # 찾은 email 후보와 직업명 사이에 다른 문자가 있으면 안됨
                    between = right[:(right.find(maybe_email))]
                    for ch in between:
                        if ch not in S_PUNCTUATION_CHARS and ch not in S_WHITE_SPACES:
                            return
                    # @ 가 없지만 email 로 인정
                    self.components["email"] = maybe_email



    def analyze_tv(self, text):
        self.components = dict()
        m1 = RE_TV_JOURNALIST.search(text)
        if m1:
            self.components["name"] = m1.group(2)
            return

        m2 = RE_YTN_JOURNALIST.search(text)
        if m2:
            self.components["name"] = m2.group(1)
            maybe_email = m2.group(2)
            if maybe_email:
                self.components["email"] = maybe_email



    def get_name(self):
        return self.components["name"] if "name" in self.components else None

    def get_email(self):
        return self.components["email"] if "email" in self.components else None

    def get_component_count(self):
        return len(self.components)

    def get_result(self):
        return self.components



# 일단은 한 라인에 2개 이상의 기자가 발견되는 경우만 처리한다.
class BylineAnalyzer(object):
    def __init__(self, text, type=BylineExtractor.GENERAL):
        self.extractors = list()
        jobs = RE_JOURNALIST_JOB.findall(text)
        if len(jobs) <= 1:
            # 바이라인은 1개만 있는 것 같은 일반적인 경우
            self.extractors.append(BylineExtractor(text, type))
            return

        # 두 기자명을 가르는 문자로 / 또는 · 등을 찾아본다.
        for i in range(1,len(jobs)):
            left = text.find(jobs[i-1]) + len(jobs[i-1])
            right = text.find(jobs[i], left)
            m = RE_BYLINE_DIV_CHARS.search(text[left:right])
            if m:
                divpos = text.find(m.group(0), left)
                byline1 = text[:divpos]
                self.extractors.append(BylineExtractor(byline1))
                text = text[divpos+1:]
            else:
                break

        self.extractors.append(BylineExtractor(text))


    def get_bylines(self):
        ret = list()
        for extr in self.extractors:
            if extr.get_component_count() > 0:
                ret.append(extr.get_result())

        return ret