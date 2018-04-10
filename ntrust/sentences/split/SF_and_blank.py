import re

from ..constants import END_CHARACERS
from .base import Sentence, SENTENCE_FLAG_SKIP

# 마침표와 공백, 일반적으로 문장의 끝부분을 나타낸다.
RE_SF_AND_DOT_DIGITS = re.compile('([\w][\w]*[{}])[\s]+'.format(''.join(map(re.escape, END_CHARACERS))))

# [SF(마침표)와 공백] 으로 문장들을 split 해서 리턴한다.
def split(sentence):
    if sentence.flag == SENTENCE_FLAG_SKIP:
        # sentence 오브젝트에 X flag가 설정되어 있다면 짜르지 않고 전체를 리턴한다.
        yield sentence
    elif not RE_SF_AND_DOT_DIGITS.search(sentence):
        # 문장이 한개만 있는 경우이다.
        yield sentence
    else:
        # 입력된 문단 텍스트를 [마침표와 공백] 으로 짤라서 각 문장을 yield 한다.
        last = 0
        for i in RE_SF_AND_DOT_DIGITS.finditer(sentence):
            yield Sentence(sentence[last:i.start()] + sentence[i.start(): i.end()])
            last = i.end()

        yield Sentence(sentence[last:])
