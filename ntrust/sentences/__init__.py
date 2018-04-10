from .split import split_sentence  # noqa


QUOTE_MARK_PAIRS = {
    '"': ('"', '”'),
    '\'': ('\'', '’'),
    '“': ('”', '"'),
    '‘': ('’', '\''),
    "''": ("''", '"'),
}

def extract_quoted(content):
    qsentences = list()
    for line in split_sentence(content, strip=True):
        for opener, closers in QUOTE_MARK_PAIRS.items():
            str = line
            while str != "":
                left = str.find(opener)
                if left < 0:
                    break

                left += len(opener)
                right = str.find(closers[0], left)
                if right < 0:
                    right = str.find(closers[1], left)

                if right < 0:
                    str = ""
                    break

                qs = str[left:right]
                if len(qs) > 0:
                    qsentences.append(qs)
                str = str[right+1:]

    return qsentences


from ..byline import S_PUNCTUATION_CHARS

def get_text_front_quote(content, quoted):
    end = content.find(quoted)
    if end <= 0:
        return ""

    end -= 1
    start = end -1
    while start >= 0 and content[start] not in S_PUNCTUATION_CHARS:
        start -= 1

    text = content[start+1:end].strip()
    return text