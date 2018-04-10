import re

from ..constants import END_CHARACERS, RE_END_CHARACERS


# 다양한 모양의 마침표 또는 물음표, 느낌표 등 문장이 끝남을 나타내는 문자들로 주어진 sentence 를 split 한다.
# 마침표 등의 뒤에는 공백이 있어야만 한다. a.b.c 처럼 공백없이 마침표가 사용되면 문장의 끝이 아닌것으로 간주되어 분리되지 않는다.
def split(sentence):
    chained = re.compile('(%s)' % '|'.join(RE_END_CHARACERS)).split(sentence.strip())

    splited = list()
    for i in chained:
        if len(splited) > 0 and i.strip() in END_CHARACERS:
            # split에 사용되었던 (마침표+공백) separator 를 뒤에 붙여준다.
            splited[-1] = splited[-1] + i.strip()
            continue

        splited.append(i.replace('\n', ' ').strip())

    return splited
