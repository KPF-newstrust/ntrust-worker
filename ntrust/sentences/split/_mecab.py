import re
import itertools
import warnings

try:
    import MeCab
except ImportError:
    MeCab = None

from .lexical import split as split_lexical
from ..constants import END_CHARACERS
from ... import tagger
from .base import SENTENCE_FLAG_SKIP, Sentence


RE_MULTIPLE_CARRIAGE_RETURN = re.compile('[\n][\s]*[\n]+', re.M)
RE_REPLACE = re.compile('(\([^\w]\))', re.M)
LIST_CHARS = (
    '■',
)
ENCLOSURES = {
    '"': ('"', '”'),
    '\'': ('\'', '’'),
    '“': ('”', '"'),
    '‘': ('’', '\''),
}
ALL_ENCLOSURES = list(ENCLOSURES.keys()) + list(itertools.chain(*ENCLOSURES.values()))
RE_SF_AND_DOT_DIGITS = re.compile('([\w][\w]*[{}])[\s]+([\d][\d]+)'.format(''.join(map(re.escape, END_CHARACERS))))


# '로 시작해서 '로 끝나는지, "로 시작해서 "로 끝나는지 등을 검사한다.
# '로 시작해서 "로 끝나는 등의 open/close 쌍이 안맞을 경우 False를 리턴
def check_enclosures(s):
    # 문장에서 따옴표 등 enclosure들만 따낸다. (일반 텍스트는 제거됨)
    found = re.compile('[{}]'.format(''.join(map(re.escape, ALL_ENCLOSURES)))).findall(s)

    es = list()
    for i in found:
        if len(es) > 0:
            # 좀전에 append한 enclosure와 같다면 닫히는 것이다. pop함
            if i in ENCLOSURES[es[-1]]:
                es.pop()
                continue

        # enclosure 열림
        if i in ENCLOSURES.keys():
            es.append(i)

    # open/close 쌍이 맞을 경우 len==0 이다.
    return len(es) < 1


def split_sentence_scan(content):
    content = content.strip()

    # 따옴표같은 인용부호 open/close 쌍이 잘 맞는지 검사
    has_valid_enclosures = check_enclosures(content)

    SL = None
    s = RE_REPLACE.search(content)
    if s:
        SL = RE_REPLACE.findall(content)
        content = RE_REPLACE.sub('{}', content.replace('{', '{{').replace('}', '}}'))

    def _return(flag, l):
        o = ''.join(l).strip()
        if SL is None:
            return Sentence(o, flag)

        cnt = o.count('{}')

        s = SL[:cnt]
        for i in range(cnt):
            SL.pop(0)

        return Sentence(o.format(*s), flag)

    # 마침표로 문장을 자른다. SF_and_blank.py 의 split 함수와 비슷한 내용?
    subs = list()
    last = None
    for i in RE_SF_AND_DOT_DIGITS.finditer(content):
        subs.append(content[last:i.start()] + i.groups()[0])
        last = i.end() - len(i.groups()[1])

    subs.append(content[last:])

    parsed = list(itertools.chain(*map(tagger.parse, subs)))

    previous_part = None
    sentence = list()
    chunk = str()
    enclosures = list()
    part = parsed.pop(0)

    flag = None
    for n, i in enumerate(content):
        if i in ('\n', '\xa0'):
            if i in ('\n',):
                ps = ''.join(sentence).strip()
                if sentence and len(list(filter(lambda x: ps.startswith(x), LIST_CHARS))) > 0:
                    yield Sentence(''.join(sentence).strip())
                    flag = None
                    sentence = list()

                    chunk = str()
                    continue

            i = ' '

        if i in (' ', '\u2028'):
            previous_part = part
            sentence.append(i)
            continue

        chunk += i
        if part and chunk == part[0]:
            sentence.append(chunk)

            if has_valid_enclosures:
                for j in chunk:
                    if j in ALL_ENCLOSURES:
                        if len(enclosures) > 0 and j in ENCLOSURES[enclosures[-1]]:
                            enclosures.pop()
                        else:
                            if j in ENCLOSURES.keys():
                                enclosures.append(j)

            if part is not None and part[1] in ('SF',):
                if not has_valid_enclosures:
                    if len(list(filter(str.strip, sentence))) > 0:
                        yield _return(flag, sentence)

                    flag = None
                    sentence = list()
                else:
                    if len(enclosures) < 1:
                        if len(list(filter(str.strip, sentence))) > 0:
                            yield _return(flag, sentence)

                        flag = None
                        sentence = list()
                    else:
                        if flag is None:
                            flag = SENTENCE_FLAG_SKIP

            elif part is not None and previous_part is not None and part[1] in ('SSC',) and previous_part[1] in ('SF',) and len(enclosures) < 1:
                if len(list(filter(str.strip, sentence))) > 0:
                    yield _return(flag, sentence)

                flag = None
                sentence = list()

            previous_part = part

            if len(parsed) < 1:
                part = None
            else:
                part = parsed.pop(0)

            chunk = str()

    if len(sentence) > 0 and len(list(filter(str.strip, sentence))) > 0:
        yield _return(flag, sentence)


def split_sentence(sentence):
    # 입력값이 빈 문장이면 빈 값을 리턴한다.
    if not sentence.strip():
        return list()

    # 문장 마침부호가 없으면 입력값을 리턴한다.
    if len(list(filter(lambda x: x in sentence, END_CHARACERS))) < 1:
        return [sentence]

    return itertools.chain(*list(map(
        split_sentence_scan,
        RE_MULTIPLE_CARRIAGE_RETURN.split(sentence),
    )))


def split(sentence):
    if sentence.flag == SENTENCE_FLAG_SKIP:
        yield sentence

    if MeCab is None:
        warnings.warn('Failed to load `MeCab` module, so run `split_sentence` without `MeCab`.', ImportWarning)

        l = split_lexical(sentence)
    else:
        l = split_sentence(sentence)

    for i in l:
        yield i
