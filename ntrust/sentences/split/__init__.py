import itertools
import functools

from ...util import clean_content, make_sentence_uid
from . import SF_and_blank
from . import _mecab
from .base import Sentence


try:
    import MeCab
except ImportError:
    MeCab = None


CHAINS = (
    _mecab.split,
    SF_and_blank.split,
)


ENCLOSURES = {
    '"': ('"', '”'),
    '\'': ('\'', '’'),
    '“': ('”', '"'),
    '‘': ('’', '\''),
}
ENCLOSURES_OPEN = list(ENCLOSURES.keys())
ENCLOSURES_CLOSE = list(itertools.chain(*ENCLOSURES.values()))
ALL_ENCLOSURES = list(ENCLOSURES.keys()) + list(itertools.chain(*ENCLOSURES.values()))


def split_sentences(content):
    ic = lambda x: itertools.chain(*x)
    fn = functools.reduce(lambda a, b: lambda x: ic(map(b, ic(map(a, x)))), CHAINS)

    return fn([Sentence(content, None)])


def split_sentence(content, with_uid=False, uid_prefix=None, strip=False):
    content = clean_content(content).strip()
    sentences = split_sentences(content)
    sentences = map(lambda x: x.strip(), sentences)

    for seq, sentence in enumerate(sentences):
        if strip:
            sentence = str(sentence)

        if with_uid:
            yield (make_sentence_uid(sentence, seq, uid_prefix), sentence)
        else:
            yield sentence
