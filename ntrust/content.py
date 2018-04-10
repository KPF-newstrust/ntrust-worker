import re
import logging

from . import sentences
from . import byline

REs_UNNECESSARY = [
    re.compile(r"^\[.*\]$"),
    re.compile(r"^■.*"),
    re.compile(r"^▶.*"),
    re.compile(r"^☞.*"),
    re.compile(r"^\[.*"),
]

# 한글이나 알파벳 없이 구문부호만으로 이루어진 문장 (군더더기)
def is_punctuation_or_space_only(line):
    for ch in line:
        if ch not in byline.S_PUNCTUATION_CHARS and ch not in byline.S_WHITE_SPACES:
            return False
    return True


def is_unnecessary(line):
    for r in REs_UNNECESSARY:
        if r.match(line):
            return True

    return is_punctuation_or_space_only(line)



################################################################################
# Media specific processors

def process_01101101(self):
    for line in self.lines:
        print("101:",line)

    self.lines[1] = ""


# ex: 멀티미디어부 multi@
RE_TEAMPART_EMAIL = re.compile(r"^(.+?[부팀]) (\w+@)$")

# 01500701: 부산일보
def process_01500701(self):
    for idx,line in reversed(list(enumerate(self.lines))):
        m = RE_TEAMPART_EMAIL.match(line)
        if m:
            self.append_bylines([{"name":m.group(1), "email":m.group(2)}])
            return True
    return False


# ex: 온라인 이슈팀 @mkculture.com
RE_TEAM_AT_MKCULTURE = re.compile(r"(.+?팀)\s(@[a-zA-Z0-9-]+[a-zA-Z0-9-.]+)")
# ex: [매일경제 스타투데이 이슈팀]
RE_MK_HEAD_TEAM = re.compile(r"^\[매일경제 (.+?팀)\]")
# ex: [매일경제 스타투데이 진현철 기자]
RE_MK_HEAD_GIJA = re.compile(r"^\[매일경제 (스타투데이 )?(.+?기자)\]")

# 02100101: 매일경제
def process_02100101(self):
    for idx,line in reversed(list(enumerate(self.lines))):
        m = RE_TEAM_AT_MKCULTURE.match(line)
        if m:
            team = byline.tail_to_head_until_punctuation_char(m.group(1))
            self.append_bylines([{"name":team, "email":m.group(2)}])
            return True
        m = RE_MK_HEAD_TEAM.match(line)
        if m:
            self.append_bylines([{"name": m.group(1)}])
            return True

        m = RE_MK_HEAD_GIJA.match(line)
        if m:
            self.append_bylines([{"name": m.group(2)}])
    return False


# ex: 원주/정태욱
RE_KW_SITE_SLASH_NAME = re.compile("^(.{2,4})\/(.{2,4})$")

# 01300101: 강원도민일보
def process_01300101(self):
    m = RE_KW_SITE_SLASH_NAME.match(self.lines[-1])
    if m:
        self.append_bylines([{"name": m.group(2)}])
        return True
    return False


RE_JM_HEAD_GIJA = re.compile("[［\[]중부매일\s(.+?)[］\]]")
RE_JM_TAIL_NAME = re.compile("\/\s(.{2,4})$")

# 01400401: 중부매일
def process_01400401(self):
    for idx,line in enumerate(self.lines):
        m = RE_JM_HEAD_GIJA.match(line)
        if m:
            self.append_bylines([{"name": m.group(1)}])
            return True

    m = RE_JM_TAIL_NAME.match(self.lines[-1])
    if m:
        self.append_bylines([{"name": m.group(1)}])
        return True

    return False


RE_YTN_TAIL_NAME_EMAIL = re.compile(r"YTN\s+(.+?)\s*\[([a-zA-Z0-9-.]+)$")
RE_YTN_TAIL_NAME_EMAIL2 = re.compile(r"^(.+?)\s*\[([a-zA-Z0-9-.]+)$")

# 08100401: YTN
def process_08100401(self):
    for reTailCheck in [RE_YTN_TAIL_NAME_EMAIL, RE_YTN_TAIL_NAME_EMAIL2]:
        m = reTailCheck.match(self.lines[-1])
        if m:
            self.append_bylines([{"name": m.group(1), "email":m.group(2)}])
            return True

    return False


RE_HERALD_HEAD_NAME = re.compile("[［\[]헤럴드(.+?)=(.+?)[］\]]")

# 02100701: 헤럴드경제
def process_02100701(self):
    m = RE_HERALD_HEAD_NAME.match(self.lines[0])
    if m:
        self.append_bylines([{"name": m.group(2)}])

    return False


RE_FNNEWS_HEAD_NAME = re.compile("[［【 \[](.+?)=(.+?) *[】］\]]")

# 02100501: 파이낸셜뉴스
def process_02100501(self):
    m = RE_FNNEWS_HEAD_NAME.match(self.lines[0])
    if m:
        self.append_bylines([{"name": m.group(2)}])

    return False



# 01100201: 국민일보 (가끔 기자,email 이 하단 두줄에 적히는 경우가 있다)
def process_01100201(self):
    bl_email = None
    for line in self.lines[::-1]:
        if byline.can_be_byline(line):
            bl = byline.BylineAnalyzer(line).get_bylines()
            if bl_email == None:
                if len(bl) >= 2:
                    self.append_bylines(bl)
                    return True
                bl_email = bl
                continue
            else:
                self.append_bylines(bl_email)
                self.append_bylines(bl)
                return True
        if is_unnecessary(line):
            self.lines.remove(line)
            continue
        break

    return False


################################################################################

_under32toNone = dict.fromkeys(range(32))

def remove_under32_control_chars(text):
    return text.translate(_under32toNone)

class Sanitizer(object):
    def __init__(self, media_id=None):
        self.bylines = list()
        self.check_top_byline = media_id in ["01400601", "01500601"]
        self.is_tv = media_id in ["08100201", "08100401","08100301"]

        if media_id == "01500701": # 부산일보
            self.custom_processor = process_01500701
        elif media_id == "02100101": # 매일경제
            self.custom_processor = process_02100101
        elif media_id == "01300101": # 강원도민일보
            self.custom_processor = process_01300101
        elif media_id == "01400401": # 중부매일
            self.custom_processor = process_01400401
        elif media_id == "08100401": # YTN
            self.custom_processor = process_08100401
        elif media_id == "02100701":  # 헤럴드경제
            self.custom_processor = process_02100701
        elif media_id == "02100501":  # 파이낸셜뉴스
            self.custom_processor = process_02100501
        elif media_id == "01100201":  # 국민일보
            self.custom_processor = process_01100201
        pass

    def get_contents(self, linesep="\n"):
        return linesep.join(self.lines)

    def get_contents_lines(self):
        return self.lines

    def get_bylines(self):
        return self.bylines if len(self.bylines) > 0 else None

    def _remove_empty_lines(self):
        newlines = list()
        empty_cnt = 0
        for line in self.lines:
            if line:
                newlines.append(line)
            else:
                empty_cnt += 1

        if empty_cnt > 0:
            self.lines = newlines


    def append_bylines(self, bls):
        if bls is None:
            return
        for bl in bls:
            if len(bl) == 0:
                continue
            dup = False
            for idx,old in enumerate(self.bylines):
                if old.get("name") == bl.get("name") and old.get("email") == bl.get("email"):
                    dup = True
                    break
            if not dup:
                self.bylines.append(bl)


    def process(self, contents):
        self.lines = list()
        if isinstance(contents, str):
            for line in sentences.split_sentence(contents, strip=True):
                line = remove_under32_control_chars(line)
                if line:
                    self.lines.append(line)
        else:
            for lines in contents:
                for line in sentences.split_sentence(lines, strip=True):
                    line = remove_under32_control_chars(line)
                    if line:
                        self.lines.append(line)

        processed = False
        if hasattr(self, "custom_processor"):
            processed = self.custom_processor(self)

        if not processed:
            if self.is_tv:
                self.detect_tv_byline()
            elif self.check_top_byline:
                self.detect_byline_from_top()
            else:
                self.detect_byline_from_bottom()

        # merge bylines if [{name},{email}] case
        if len(self.bylines) == 2 and len(self.bylines[0]) == 1 and len(self.bylines[1]) == 1:
            if not self.bylines[0].keys() == self.bylines[1].keys():
                self.bylines[0].update(self.bylines[1])
                self.bylines.pop()

        self._remove_empty_lines()
        # done


    def detect_byline_from_bottom(self):
        for line in self.lines[::-1]:
            if is_unnecessary(line):
                self.lines.remove(line)
                continue
            if byline.can_be_byline(line):
                self.append_bylines(byline.BylineAnalyzer(line).get_bylines())
                return
            break

    def detect_byline_from_top(self):
        for line in self.lines:
            if byline.can_be_byline(line):
                self.append_bylines(byline.BylineAnalyzer(line).get_bylines())
                return
            if is_unnecessary(line):
                self.lines.remove(line)
                continue
            break

    def detect_tv_byline(self):
        self.append_bylines(byline.BylineAnalyzer(self.lines[-1], byline.BylineExtractor.TV).get_bylines())
