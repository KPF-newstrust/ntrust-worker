import uuid
import MeCab
import itertools

from ..util import clean_content


TAGGER = None
TAG_BLANK = 'BB'
TAG_END_OF_SENTENCE = 'SS_'
FLAG_SPLIT = '-'
FLAG_MERGED = 'M'
FLAG_COMPOUND = '+'


# 입력 단어와 해당 단어의 품사 태깅 코드를 리턴한다. 예: ['달러', 'NNBC']
def split_feature(l):
    word, feature = l.split('\t', 1)
    return [word, feature.split(',')[0]]  # (word, feature(s))

# deep 파싱을 하면 MeCab 에서 + 로 합쳐진 것으로 분석된 품사를 나눈다.
# 품사만 나눠지고 원문 단어 및 uid 등은 중복 사용된다.
# 예: '사들였','VV+EP' --> [['사들였', 'VV', [], 'uid'], ['사들였', 'EP', [], 'uid']]
def deep_parse_tag(o):
    word, tag, flags, uid = o
    if '+' not in tag:
        return [[word, tag, flags, uid]]

    if FLAG_COMPOUND not in flags:
        flags.append(FLAG_COMPOUND)

    n = tag.split(u'+')
    return list(map(list, zip([word] * len(n), n, [flags] * len(n), [uid] * len(n))))


def parse(c, deep=False):
    global TAGGER

    if TAGGER is None:
        TAGGER = MeCab.Tagger()

    c = clean_content(c)

    # TAGGER.parse() 를 거치면 MeCab 형태소 분석이 처리된다.
    # 리턴 스트링엔 \n 으로 각 형태소 정보가 구분되고
    # 각 형태소 정보는 \t 으로 원문 및 품사코드 등이 구분되어 있다.
    # (마지막으로 의미없는 \n 가 붙어 있으므로 [:-1] 처리를 한다.)
    parsed = filter(str.strip, TAGGER.parse(c).rstrip().split('\n')[:-1])

    # featured 는 [단어,품사]로 split_feature된 각 형태소에 [] 와 uuid 를 붙여
    # ['달러', 'NNBC', [], '92a11fe6121b11e785afb8e8563cd83c'] 처럼 생긴 것들의 배열이 된다.
    featured = map(
        lambda x: x[1] + [list()] + [uuid.uuid1().hex],
        filter(lambda x: x[1][0].strip(), enumerate(map(split_feature, parsed))),
    )

    if not deep:
        return list(featured)

    return itertools.chain(*map(deep_parse_tag, featured))


def parse_with_end_of_sentence(c, deep=False):
    for i in parse(c, deep=deep):
        yield i

    yield ['', TAG_END_OF_SENTENCE, list(), uuid.uuid1().hex]  # `SS_` means the end of sentence.


def parse_by_sentence(c, deep=False):
    from ..sentences import split_sentence

    return itertools.chain(*map(
        lambda x: parse_with_end_of_sentence(x, deep=deep),
        split_sentence(c, strip=True),
    ))


# 명사 두개가 인접할 경우 서로 합친다. (예: 미국,돈 -> 미국돈)
def _merge_NNG_NNPs(pool, tag, word):
    if len(pool) < 1:
        return None

    # NNG=일반명사, NNP=고유명사
    if tag not in ('NNG', 'NNP'):
        return None

    if 'NNG' not in pool[-1][1] and 'NNP' not in pool[-1][1]:
        return None

    # 합쳐진 품사는 NNP 가 있다면 NNP로 대표한다. (예: NNP+NNG -> NNP)
    pool[-1][2] = [FLAG_SPLIT]
    surplus = [
        '{}{}'.format(pool[-1][0], word),
        ['NNP'] if 'NNP' in ([tag] + pool[-1][1]) else [tag],
        [FLAG_MERGED],
    ]

    return (pool, surplus)


# 숫자+명사 를 합친다. (예: 8,기 -> 8기)
def _merge_NNG_SN(pool, tag, word):
    if len(pool) < 1:
        return None

    if tag not in ('NNG',):
        return None

    # SN=숫자
    if 'SN' not in pool[-1][1]:
        return None

    pool[-1][2] = [FLAG_SPLIT]
    surplus = [
        '{}{}'.format(pool[-1][0], word),
        pool[-1][1] + [tag],
        [FLAG_MERGED],
    ]

    return (pool, surplus)


# ETN은 앞의 명사와 붙여준다. (예: 돕,기 -> 돕기)
def _merge_ETN(pool, tag, word):
    if len(pool) < 1:
        return None

    # ETN=명사형 전성 어미
    if tag not in ('ETN',):
        return None

    pool[-1][2] = [FLAG_SPLIT]
    surplus = [
        '{}{}'.format(pool[-1][0], word),
        ['NNG'],
        [FLAG_MERGED],
    ]

    return (pool, surplus)


# ETM 앞에 동사 파생 접미사, 형용사가 있을때 합쳐준다. (예: 없,는 -> 없는)
def _merge_ETM_and_XSV_VA(pool, tag, word):
    if len(pool) < 1:
        return None

    # ETM=관형형 전성 어미
    if tag not in ('ETM',):
        return None

    # XSV=동사 파생 접미사, VA=형용사
    if not (set(('XSV', 'VA')) & set(pool[-1][1])):
        return None

    pool[-1][2] = [FLAG_SPLIT]
    surplus = [
        '{}{}'.format(pool[-1][0], word),
        pool[-1][1] + [tag],
        [FLAG_MERGED],
    ]

    return (pool, surplus)


# 연결 어미를 앞 품사와 붙여준다. (예: 사들였,다 -> 사들였다)
def _merge_EF_EC_and_etc(pool, tag, word):
    if len(pool) < 1:
        return None

    # EF=종결 어미, EC=연결 어미
    if tag not in ('EF', 'EC'):
        return None

    # VA=형용사, VV=동사, VF=???, VX=보조용언, XSV+EP=동사파생 접미사+선어말 어미, VV+EP=동사+선어말 어미
    if not (set(pool[-1][1]) & set(('VA', 'VV', 'VF', 'VX', 'XSV+EP', 'VV+EP'))):
        return None

    pool[-1][2] = [FLAG_SPLIT]
    new_word = '{}{}'.format(pool[-1][0], word)
    new_tag = pool[-1][1] + [tag]
    # NNG=일반명사
    if len(pool) > 1 and pool[-2][1] in ('NNG',):
        pool[-2][2] = FLAG_SPLIT
        new_word = pool[-2][0] + new_word
        new_tag = pool[-2][1] + new_tag

    surplus = [new_word, new_tag, FLAG_MERGED]

    return (pool, surplus)


# NNBC 일때, 앞 품사가 특정조건이면 합친다. (예: 950만,달러 -> '950만 달러')
def _merge_NNBC(pool, tag, word):
    if len(pool) < 1:
        return None

    # NNBC=단위를 나타내는 명사 (예: 달러)
    if tag not in ('NNBC',):
        return None

    # NNBC 앞이 공백이면 그 공백 앞쪽을 타겟으로 한다.
    blank = ''
    target = pool[-1]
    if set(target[1]) & set((TAG_BLANK,)):
        target = pool[-2]
        blank = ' '

    # NNG=일반명사, NNP=고유명사, SN=숫자,
    if not (set(target[1]) & set(('NNG', 'NNP', 'SN'))):
        return None

    target[2].append(FLAG_SPLIT)
    surplus = [
        '{}{}{}'.format(target[0], blank, word),
        target[1] + [tag],
        [FLAG_MERGED],
    ]

    return (pool, surplus)


def _merge_NR_and_SN_NNG_NNP(pool, tag, word):
    if len(pool) < 1:
        return None

    # NR=수사 (예: 백,천,만)
    if tag not in ('NR',):
        return None

    # NNG=일반명사, NNP=고유명사, SN=숫자,
    if not (set(pool[-1][1]) & set(('NNG', 'NNP', 'SN'))):
        return None

    pool[-1][2] = [FLAG_SPLIT]
    surplus = [
        '{}{}'.format(pool[-1][0], word),
        pool[-1][1] + [tag],
        [FLAG_MERGED],
    ]

    return (pool, surplus)



CHAINED_MERGE = (
    _merge_NNG_NNPs,
    _merge_NNG_SN,
    _merge_ETN,
    _merge_ETM_and_XSV_VA,
    _merge_EF_EC_and_etc,
    _merge_NNBC,
    _merge_NR_and_SN_NNG_NNP,
)


# SSO,SSC 쌍을 찾아 yield 한다. SSO 없이 SSC 가 먼저 발견될 경우 무시한다.
# 일단은 (a(b)c) 처럼 겹치는 ()에서 바깥 쪽은 무시한다.
# NNP,NNG 합치는 것이 목적인데 () 안의 ()의 경우 바깥 ()가 NNP,NNG 조건에 안맞을 것으로 예상되기 때문..
def each_ss_open_closes(pool):
    idxOpen = -1
    for idx,item in enumerate(pool):
        if 'SSO' in item[1]:
            idxOpen = idx
            continue

        if 'SSC' in item[1]:
            if idxOpen >= 0:
                yield idxOpen, idx
                idxOpen = -1
                continue


# NNP=고유명사, NNG=일반명사, SSO,SSC=괄호 열기,닫기
def _merge_NNP_NNG_in_SSOC(pool,idxOpen,idxClose):
    # split 되지 않은 항목들만 모아본다.
    nonSplits = list()
    for idx,elm in itertools.islice(enumerate(pool), idxOpen+1, idxClose):
        if elm[2] and FLAG_SPLIT in elm[2]:
            continue
        nonSplits.append((idx,elm))

    if len(nonSplits) == 0:
        return

    for rseq,tup in enumerate(reversed(nonSplits)):
        idxNng, nng = tup[0], tup[1]
        if not 'NNG' in nng[1]:
            continue
        if FLAG_SPLIT in nng[2]:
            continue    # 이전 merge에 사용되었다. (별로 필요없을것 같지만..)

        # NNG 가 발견되었다. 그 앞에 NNP가 있다면 합친다.
        seq = len(nonSplits) - rseq -1
        target = None if seq < 1 else nonSplits[seq-1][1]
        if target == None:
            return

        blank = ''
        if TAG_BLANK in target[1]:
            blank = target[0]
            target = None if seq<2 else nonSplits[seq-2][1]
            if target == None:
                return

        if not 'NNP' in target[1]:
            continue    # 꽝~ NNP,NNG 시퀀스가 아니군요.

        # 기존의 target(nnp) 과 nng 에는 FLAG_SPLIT 을 추가해준다.
        target[2].append(FLAG_SPLIT)
        nng[2].append(FLAG_SPLIT)
        surplus = [
            '{}{}{}'.format(target[0], blank, nng[0]),
            target[1] + nng[1],
            [FLAG_MERGED],
            nng[3]
        ]

        # 새로 만들어진 surplus 를 nng 뒤쪽에 삽입한다.
        pool.insert(idxNng+1, surplus)



def _merge(sentence, tags):
    tags = list(tags)
    sentence = list(sentence)
    k = list()
    chunk = str()
    word = None
    uid = None
    previous_uid = None
    while True:
        if len(sentence) < 1:
            if len(chunk.strip()) < 1:
                break
        else:
            if len(sentence[0].strip()) < 1:
                k.append([' ', [TAG_BLANK], None, None])
                sentence.pop(0)
                continue

        try:
            word, tag, flags, uid = tags[0]
        except IndexError:
            break

        if uid == previous_uid:
            previous_uid = uid
            try:
                tags.pop(0)
            except IndexError:
                break

            continue

        merged = False
        if len(sentence) == 0:
            break   # 2017-08-16 shkim
        i = sentence.pop(0)
        chunk += i

        if chunk == word:
            surplus = None

            for func in CHAINED_MERGE:
                _r = func(k, tag, word)
                if _r is None:
                    continue

                k, surplus = _r
                surplus.append(uid)
                merged = True

            k.append([word, [tag], [FLAG_SPLIT] if merged else list(), uid])
            if surplus:
                k.append(surplus)

            chunk = str()
            try:
                previous_uid = uid
                tags.pop(0)
            except IndexError:
                break

    # NT-112-the-enclosed-words-must-be-tagged
    # SSO,SSC (괄호) 안의 NNP,NNG가 인접할 경우 합쳐준다.
    for ssOpen,ssClose in each_ss_open_closes(k):
        _merge_NNP_NNG_in_SSOC(k, ssOpen,ssClose)

    def make_tag_list(o):
        o[1] = [o[1]]

        return o

    if len(tags) > 0:
        k.extend(map(make_tag_list, tags))

    return k


def merge(content, deep=True, flatten_tags=False):
    from ntrust.sentences import split_sentence

    merged = list()
    for sentence in split_sentence(content):
        tags = parse_with_end_of_sentence(sentence, deep=deep)

        merged.extend(filter(lambda x: TAG_BLANK not in x[1], _merge(sentence, tags)))

    if flatten_tags:
        def make_tags_flatten(o):
            o[1] = '+'.join(o[1])

            return o

        return map(make_tags_flatten, merged)

    return merged
