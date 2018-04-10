import re
import MeCab

TAGGER = None

def get_word_and_tags_list(raw):
    global TAGGER

    if TAGGER is None:
        TAGGER = MeCab.Tagger()

    postags = list()
    for item in TAGGER.parse(raw).rstrip().split('\n')[:-1]:
        sp1 = item.split('\t')
        word = sp1[0]
        info = sp1[1].split(',')
        if info[7] == '*':
            postags.append((word, [(word, info[0])]))
            continue

        subtags = list()
        for stag in info[7].split("+"):
            sp2 = stag.split("/")
            subtags.append((sp2[0], sp2[1]))

        postags.append((word, subtags))

    return postags

# pos가 * 일때는 다음 pos가 맞을때까지 단어가 안맞아도 pass할 수 있다.
# 단 카운터를 두고 무제한 pass 하지 않도록 한다.
# 마지막 pos는 * 이면 안된다.
anonpred_patterns = [
    # [ (word,pos), (word,pos) ... ]
    # 무주체 술어 -->
    [("알리", "VV"), ("어", "EC"), ("지", "VX"), ("*", "EP"), ("*", "EF")],  # 알려졌다
    [("전하", "VV"), ("아", "EC"), ("지", "VX"), ("*", "EP"), ("*", "EF")],  # 전해졌다
    [("밝히", "VV"), ("어", "EC"), ("지", "VX"), ("*", "EP"), ("*", "EF")],  # 밝혀졌다
    [("강조", "NNG"), ("되", "XSV"), ("*", "EP"), ("*", "EF")],  # 강조됐다
    [("지적", "NNG"), ("되", "XSV"), ("*", "EP"), ("*", "EF")],  # 지적됐다
    # 주관적 술어 -->
    [("주장", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 주장했다
    [("주장", "NNG"), ("을", "JKO"), ("내놓", "VV"), ("*", "EP"), ("*", "EF")],  # 주장을 내놨다
    [("강조", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 강조했다
    [("선언", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 선언했다
    [("당부", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 당부했다
    [("호소", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 호소했다
    [("바람", "NNG"), ("을", "JKO"), ("나타내", "VV"), ("*", "EP"), ("*", "EF")],  # 바람을 나타냈다
    [("하소연", "NNG"), ("하", "VV"), ("*", "EP"), ("*", "EF")],  # 하소연했다
    [("아쉽", "VA"), ("어", "EC"), ("하", "VX"), ("*", "EP"), ("*", "EF")],  # 아쉬워했다
    [("안타깝", "VA"), ("어", "EC"), ("하", "VX"), ("*", "EP"), ("*", "EF")],  # 안타까워했다
    [("우려", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 우려했다
    [("우려", "NNG"), ("를", "JKO"), ("표명", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 우려를 표명했다
    [("단언", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 단언했다
    [("단정", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 단정했다
    [("일축", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 일축했다
    [("고수", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 고수했다
    [("분명히", "MAG"), ("하", "VV"), ("*", "EP"), ("*", "EF")],  # 분명히했다
    [("촉구", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 촉구했다
    [("경고", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 경고했다
    [("으름", "NNG"), ("장", "NNG"), ("을", "JKO"), ("놓", "VV"), ("*", "EP"), ("*", "EF")],  # 으름장을 놨다
    [("압박", "NNG"), ("을", "JKO"), ("가하", "VV"), ("*", "EP"), ("*", "EF")],  # 압박을 가했다
    [("지적", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 지적했다
    [("꼬집", "VV"), ("*", "EP"), ("*", "EF")],  # 꼬집었다
    [("비판", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 비판했다
    [("비난", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 비난했다
    [("해명", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 해명했다
    [("반발", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 반발했다
    [("항변", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 항변했다
    [("불쾌", "NNG"), ("감", "NNG"), ("을", "JKO"), ("표시", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 불쾌감을 표시했다
    [("목", "NNG"), ("소리", "NNG"), ("를", "JKO"), ("높이", "VV"), ("*", "EP"), ("*", "EF")],  # 목소리를 높였다
    [("의혹", "NNG"), ("을", "JKO"), ("제기", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 의혹을 제기했다
    [("의문", "NNG"), ("을", "JKO"), ("제기", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 의문을 제기했다
    [("의아", "NNG"), ("하", "XSV"), ("아", "EC"), ("하", "VX"), ("*", "EP"), ("*", "EF")],  # 의아해했다
    [("문제", "NNG"), ("를", "JKO"), ("제기", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 문제를 제기했다
    [("시사", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 시사했다
    [("내다보", "VV"), ("*", "EP"), ("*", "EF")],  # 내다봤다
    [("내", "VX"), ("다", "EC"), ("보", "VX"), ("*", "EP"), ("*", "EF")],  # 내다봤다
    [("내비치", "VV"), ("*", "EP"), ("*", "EF")],  # 내비쳤다
    [("전망", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 전망했다
    [("기대", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 기대했다
    [("기대", "NNG"), ("를", "JKO"), ("나타내", "VV"), ("*", "EP"), ("*", "EF")],  # 기대를 나타냈다
    [("관측", "NNG"), ("도", "JX"), ("나오", "VV"), ("고", "EC"), ("있", "VX"), ("*", "EF")],  # 관측도 나오고 있다
    [("평하", "VV"), ("*", "EP"), ("*", "EF")],  # 평했다
    [("평가", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 평가했다
    [("분석", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 분석했다
    [("이라고", "JKQ"), ("도", "JX"), ("하", "VV"), ("*", "EP"), ("*", "EF")],  # 라고도 했다
    [("말", "NNG"), ("하", "XSV"), ("ᆯ", "ETM"), ("정도", "NNG"), ("이", "VCP"), ("*", "EF")],  # 말할 정도다
    [("털어놓", "VV"), ("*", "EP"), ("*", "EF")],  # 털어놓았다
    [("토로", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 토로했다
    [("귀", "NNG"), ("띔", "NNG"), ("하", "XSV"), ("*", "EP"), ("*", "EF")],  # 귀띔했다
    [("벌어지", "VV"), ("ᆫ", "ETM"), ("입", "NNG"), ("을", "JKO"), ("다물", "VV"), ("지", "EC"), ("못하", "VX"), ("*", "EP"), ("*", "EF")],  # 벌어진 입을 다물지 못했다
    [("말", "NNG"), ("을", "JKO"), ("제대로", "MAG"), ("잇", "VV"), ("지", "EC"), ("못하", "VX"), ("*", "EP"), ("*", "EF")],  # 말을 제대로 잇지 못했다
    [("입", "NNG"), ("을", "JKO"), ("모으", "VV"), ("*", "EP"), ("*", "EF")],  # 입을 모았다
    [("자조", "NNG"), ("적", "XSN"), ("이", "VCP"), ("ᆫ", "ETM"), ("태도", "NNG"), ("를", "JKO"), ("보이", "VV"), ("*", "EP"), ("*", "EF")],  # 자조적인 태도를 보였다
    [("흥분", "NNG"), ("을", "JKO"), ("감추", "VV"), ("지", "EC"), ("못하", "VX"), ("*", "EP"), ("*", "EF")],  # 흥분을 감추지 못했다
    [("망설이", "VV"), ("*", "EP"), ("*", "EF")],  # 망설였다
    [("한", "MM"), ("마디", "NNBC"), ("더", "MAG"), ("붙이", "VV"), ("*", "EP"), ("*", "EF")],  # 한마디 더 붙였다
    [("한", "NNG"), ("숨", "NNG"), ("을", "JKO"), ("쉬", "VV"), ("*", "EP"), ("*", "EF")],  # 한숨을 쉬었다
    [("혀", "NNG"), ("를", "JKO"), ("내두르", "VV"), ("*", "EP"), ("*", "EF")],  # 혀를 내둘렀다
    [("완화", "NNG"), ("되", "XSV"), ("ᆫ", "ETM"), ("어조", "NNG"), ("로", "JKB"), ("나오", "VV"), ("*", "EP"), ("*", "EF")],  # 완화된 어조로 나왔다
    [("신중", "NNG"), ("하", "XSA"), ("ᆫ", "ETM"), ("반응", "NNG"), ("을", "JKO"), ("보이", "VV"), ("*", "EP"), ("*", "EF")],  # 신중한 반응을 보였다

]

class PosPatternMatcher(object):
    def __init__(self, pattern):
        self.pattern = pattern
        self.idxEnd = len(pattern)
        self.idx = 0
        self.pass_count = 0

    # 패턴 매칭이 최종 실패라고 판단되면 False 를 리턴한다.
    # True를 리턴하면 아직 성공 가능성이 있는 것이다.
    def push(self, word, pos):
        ptn_word = self.pattern[self.idx][0]
        ptn_pos = self.pattern[self.idx][1]
        #print("input(%s,%s) vs ptn(%s,%s)" % (word,pos, ptn_word,ptn_pos))
        if ptn_pos == '*':
            ptn_pos = self.pattern[self.idx +1][1]
            if pos == ptn_pos:
                # 다음 pos 에 도달했다.
                self.idx += 1
                ptn_word = self.pattern[self.idx][1]
            else:
                self.pass_count += 1
                return (self.pass_count <= 3)
        elif ptn_pos != pos:
            # pos not matched
            return False

        if ptn_word != '*' and ptn_word != word:
            # word not matched
            return False

        self.idx += 1
        self.pass_count = 0
        return True

    # 위 push 메소드는 최종 성공 여부를 알려주지 않으므로 성공후 is_ended 를 호출해서 끝났는지 체크한다.
    def is_ended(self):
        return (self.idx == len(self.pattern))



anonpred_ptn_map = dict()

# 텍스트 raw에서 무주체술어 및 주관적 술어를 모두 찾아 배열로 리턴한다.
def find_anonymous_predicates(raw):
    global anonpred_ptn_map
    if len(anonpred_ptn_map) == 0:
        for ptn in anonpred_patterns:
            first_word = ptn[0][0]
            if first_word in anonpred_ptn_map:
                anonpred_ptn_map[first_word].append(ptn)
            else:
                anonpred_ptn_map[first_word] = [ptn]

    ret = list()
    postags = get_word_and_tags_list(raw)
    cnt = len(postags)
    for idx in range(cnt):
        first_word = postags[idx][1][0][0]
        if first_word not in anonpred_ptn_map:
            continue

        for ptrn in anonpred_ptn_map[first_word]:
            ppm = PosPatternMatcher(ptrn)
            phrase = ""
            i = idx
            while i < cnt:
                src = postags[i]
                i += 1
                phrase += src[0]
                subtags = src[1]
                for stag in subtags:
                    if ppm.push(stag[0], stag[1]) == False:
                        i = cnt
                        break
                    if ppm.is_ended():
                        ret.append(phrase)
                        #print("Finally matched: " + phrase)
                        i = cnt
                        break

    return ret
