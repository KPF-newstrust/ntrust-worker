import re
import html
import hashlib


RE_USELESS_CHARS = (
    (lambda x: '\xa0' in x, re.compile('\xa0'), ' '),
    (lambda x: '\xeb' in x, re.compile('\xeb'), ' '),
    (lambda x: '\u3000' in x, re.compile('\u3000'), ' '),
    (lambda x: '\u2028' in x, re.compile('\u2028'), ' '),
    (lambda x: '\u2029' in x, re.compile('\u2029'), ' '),
)

# 이상한 공백문자를 표준 공백문자 ' '로 치환하고 strip 한다.
def clean_content(c, strip=False):
    for check, re_sub, sub in RE_USELESS_CHARS:
        if not check(c):
            continue

        c = re_sub.sub(sub, c)

    if strip:
        c = c.strip()

    return c


def strip_html_entities(c):
    return html.unescape(c)


def make_sentence_uid(sentence, seq, prefix=None):
    return '{}:{}:{}'.format(
        prefix if prefix else '0',
        seq,
        hashlib.md5(sentence.encode('utf-8')).hexdigest(),
    )
