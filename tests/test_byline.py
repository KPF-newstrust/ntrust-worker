import unittest
import re
import os
import glob

#from ntrust import sentences
from ntrust import sanitizer
from ntrust import byline
import ntrust.content

import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('ntrust.sanitizer').setLevel(logging.DEBUG)

RE_SAMPLE_FILENUM = re.compile(r"(.+)-input\.txt")

def byline_samples():
    curdir = os.path.dirname(os.path.abspath(__file__))
    dataglob = os.path.join(curdir, "byline", "*-input.txt")
    for datafilename in glob.glob(dataglob):
        if "skeleton" in datafilename:
            continue

        with open(datafilename, 'r', encoding='utf-8') as dfile:
            m = RE_SAMPLE_FILENUM.match(datafilename)
            if m is None:
                raise RuntimeError("Invalid datafile name: " + datafilename)

            sample = dict()
            num = m.group(1)
            sample["num"] = num[num.rfind(os.sep)+1:]
            if sample["num"] in ["048"]:
                continue

            if sample["num"] not in ["065"]:
                continue

            try:
                sani_lines = list()
                stfilename = m.group(1) + "-sanitized.txt"
                with open(stfilename) as stfile:
                    for line in stfile:
                        if line:
                            sani_lines.append(line)
            except:
                pass

            sample["sanitized_lines"] = sani_lines

            for line in dfile:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("-"):
                    break
                colon = line.find(":")
                if colon < 0:
                    raise RuntimeError("Invalid byline data file:" + datafilename)
                key = line[:colon].strip()
                val = line[(colon+1):].strip()
                sample[key] = val

            contents = []
            for cline in dfile:
                contents.append(cline)
            sample["contents"] = "".join(contents)

            try:
                #sample["byline_names"] = [x.strip() for x in sample["byline_name"].split(",")]
                #sample["byline_emails"] = [x.strip() for x in sample["byline_email"].split(",")]
                byline_names = [x.strip() for x in sample["byline_name"].split(",")]
                byline_emails = [x.strip() for x in sample["byline_email"].split(",")]

                bylines = list()
                for i in range(0, len(byline_names) or len(byline_emails)):
                    bylines.append(dict())
                for i, bn in enumerate(byline_names):
                    if bn:
                        bylines[i]["name"] = bn
                for i, be in enumerate(byline_emails):
                    if be:
                        bylines[i]["email"] = be
                sample["bylines"] = bylines

                sample["mediaId"] = sample["news_id"].split(".")[0]
            except KeyError:
                raise RuntimeError("Some required field is missing in byline data file: " + datafilename)

            yield sample

    print("Done")


class TestBylineExtract(unittest.TestCase):

    def xtest_byline_helpers(self):
        self.assertEqual(byline.find_likely_email("abc@def.com"), "abc@def.com")
        self.assertEqual(byline.find_likely_email(" abc@def.com "), "abc@def.com")
        self.assertEqual(byline.find_likely_email("==abc@def.com=="), "abc@def.com")
        self.assertEqual(byline.find_likely_email("홍길동 기자 abc@def.com"), "abc@def.com")
        self.assertEqual(byline.find_likely_email("a.b_c-d@def.com"), "a.b_c-d@def.com")
        self.assertEqual(byline.find_alpha_numeric("고길동 기자 abcd"), "abcd")
        self.assertEqual(byline.find_journalist_job("고길동 기자 abcd"), "기자")
        self.assertEqual(byline.find_journalist_job("고길동 인턴기자 abcd"), "인턴기자")
        self.assertEqual(byline.find_journalist_job("고길동 논설위원"), "논설위원")

    def xtest_byline_analyze(self):
        self.assertEqual(byline.tail_to_head_until_punctuation_char(".ABCD "), "ABCD ")
        self.assertEqual(byline.tail_to_head_until_punctuation_char("/김길동 기자 "), "김길동 기자 ")
        self.assertEqual(byline.tail_to_head_until_punctuation_char("했다. 김길동 기자 "), "김길동 기자 ")
        self.assertEqual(byline.tail_to_head_until_punctuation_char("[아시아투데이 박아람 "), "아시아투데이 박아람 ")
        self.assertEqual(byline.tail_to_head_until_punctuation_char("순천/양선아"), "양선아")
        self.assertEqual(byline.head_to_tail_until_punctuation_char("ABC/"), "ABC")
        self.assertEqual(byline.head_to_tail_until_punctuation_char(" ABC/  "), " ABC")
        self.assertEqual(byline.head_to_tail_until_punctuation_char("/"), "")
        self.assertEqual(byline.head_to_tail_until_punctuation_char("A/B"), "A")
        self.assertEqual(byline.head_to_tail_until_punctuation_char("A B C.D/B"), "A B C")
        self.assertEqual(byline.normalize_name_with_job("양홍주","기자"), "양홍주 기자")
        self.assertEqual(byline.normalize_name_with_job("김길동 ", "기자"), "김길동 기자")
        self.assertEqual(byline.normalize_name_with_job("김길동 수습", "기자"), "김길동 수습기자")

        self.assertEqual(byline.BylineAnalyzer("김동진·박세준 기자 bluewins@segye.com").get_bylines(), [{"name":"김동진·박세준 기자", "email":"bluewins@segye.com"}])
        self.assertEqual(byline.BylineAnalyzer("안진용 기자 realyong@munhwa.com").get_bylines(), [{"name":"안진용 기자", "email":"realyong@munhwa.com"}])
        self.assertEqual(byline.BylineAnalyzer("순천/양선아 기자").get_bylines(), [{"name":"양선아 기자"}])
        self.assertEqual(byline.BylineAnalyzer("김능현기자 nhkimchn").get_bylines(), [{"name": "김능현 기자", "email":"nhkimchn"}])
        self.assertEqual(byline.BylineAnalyzer("줄 것으로 보인다. 양홍주기자 ").get_bylines(), [{"name": "양홍주 기자"}])
        self.assertEqual(byline.BylineAnalyzer("파주=김요섭기자").get_bylines(), [{"name": "김요섭 기자"}])
        self.assertEqual(byline.BylineAnalyzer("글/신창윤기자 shincy21@kyeongin.com").get_bylines(), [{"name": "신창윤 기자", "email":"shincy21@kyeongin.com"}])
        self.assertEqual(byline.BylineAnalyzer("글/신창윤기자 shincy21@kyeongin.com · 사진/강승호기자 kangsh@kyeongin.com").get_bylines(), [{"name": "신창윤 기자", "email":"shincy21@kyeongin.com"},{"name": "강승호 기자", "email":"kangsh@kyeongin.com"},])
        self.assertEqual(byline.BylineAnalyzer("원주/박성준 kwwin@kado.net").get_bylines(), [{"name": "박성준", "email":"kwwin@kado.net"}])
        self.assertEqual(byline.BylineAnalyzer("이라고 말했다. 내포=강제일 기자 kangjeil@").get_bylines(), [{"name": "강제일 기자", "email":"kangjeil@"}])
        self.assertEqual(byline.BylineAnalyzer("[신찬옥 기자 / 이영욱 기자]").get_bylines(), [{'name': '신찬옥 기자'}, {'name': '이영욱 기자'}])

        # check 014
        # 오는 11월까지 진행한다. / 김금란
        # ^[충청일보 이정규기자]
        # ^[옥천=충청일보 이능희기자]
        self.assertEqual(byline.BylineAnalyzer("/김병학기자").get_bylines(), [{"name": "김병학 기자"}])
        self.assertEqual(byline.BylineAnalyzer("영동 / 손근방기자").get_bylines(), [{"name": "손근방 기자"}])
        self.assertEqual(byline.BylineAnalyzer("예산=강명구 기자 kmg119sm@cctoday.co.kr").get_bylines(), [{"name": "강명구 기자", "email":"kmg119sm@cctoday.co.kr"}])
        self.assertEqual(byline.BylineAnalyzer("이라고 밝혔다. 정오복 기자").get_bylines(), [{"name": "정오복 기자"}])
        self.assertEqual(byline.BylineAnalyzer("정다은 수습기자 ksdaeun@ksilbo.co.kr").get_bylines(), [{"name": "정다은 수습기자", "email":"ksdaeun@ksilbo.co.kr"}])
        self.assertEqual(byline.BylineAnalyzer("박해철 수습기자").get_bylines(), [{"name": "박해철 수습기자"}])
        self.assertEqual(byline.BylineAnalyzer("테스트를 실시했다. 이석주 기자 serenom@kookje.co.kr").get_bylines(), [{"name": "이석주 기자", "email":"serenom@kookje.co.kr"}])
        self.assertEqual(byline.BylineAnalyzer("아쉬움을 삼켜야 했다. 안인석 기자 doll@kookje.co.kr").get_bylines(), [{"name": "안인석 기자", "email":"doll@kookje.co.kr"}])
        # ^포항 이상원 기자 seagull@msnet.co.kr (030)
        self.assertEqual(byline.BylineAnalyzer("황상욱 기자 eyes@").get_bylines(), [{"name": "황상욱 기자", "email":"eyes@"}])
        self.assertEqual(byline.BylineAnalyzer("이영란기자 yrlee@yeongnam.com").get_bylines(), [{"name": "이영란 기자", "email":"yrlee@yeongnam.com"}])
        self.assertEqual(byline.BylineAnalyzer("관리번호로 신고하는 방법을 홍보했다. 박광일기자").get_bylines(), [{"name": "박광일 기자"}])
        self.assertEqual(byline.BylineAnalyzer("/여수=김창화기자 chkim@").get_bylines(), [{"name": "김창화 기자", "email":"chkim@"}])
        self.assertEqual(byline.BylineAnalyzer("/김대성기자 bigkim@").get_bylines(), [{"name": "김대성 기자", "email":"bigkim@"}])
        self.assertEqual(byline.BylineAnalyzer("서울=김선욱 기자 swkim@jnilbo.com").get_bylines(), [{"name": "김선욱 기자", "email":"swkim@jnilbo.com"}])
        self.assertEqual(byline.BylineAnalyzer("최선을 다 하겠다”고 말했다. 김제=최대우 기자").get_bylines(), [{"name": "최대우 기자"}])
        #self.assertEqual(byline.BylineAnalyzer("[디지털뉴스국 김경택 기자]").get_bylines(), [{"name": "김경택 기자"}])
        self.assertEqual(byline.BylineAnalyzer("/전종선기자 jjs7377").get_bylines(), [{"name": "전종선 기자", "email":"jjs7377"}])
        self.assertEqual(byline.BylineAnalyzer("상점이 운영중이다. /대전=박희윤기자 hypark").get_bylines(), [{"name": "박희윤 기자", "email":"hypark"}])
        self.assertEqual(byline.BylineAnalyzer("/서민우기자 ingaghi").get_bylines(), [{"name": "서민우 기자", "email":"ingaghi"}])
        self.assertEqual(byline.BylineAnalyzer("증시분석 전문기자 로봇 ET etbot@etnews.com ").get_bylines(), [{"name": "증시분석 전문기자 로봇 ET", "email":"etbot@etnews.com"}])
        self.assertEqual(byline.BylineAnalyzer("신명진 IP노믹스 기자 mjshin@etnews.com ").get_bylines(), [{"name": "신명진 IP노믹스 기자", "email":"mjshin@etnews.com"}])
        self.assertEqual(byline.BylineAnalyzer("/ parksm@fnnews.com 박선민 기자").get_bylines(), [{"name": "박선민 기자", "email":"parksm@fnnews.com"}])
        self.assertEqual(byline.BylineAnalyzer("fact0514@fnnews.com 김용훈 기자").get_bylines(), [{"name": "김용훈 기자", "email":"fact0514@fnnews.com"}])
        self.assertEqual(byline.BylineAnalyzer("곽경민 한경닷컴 연예이슈팀 기자").get_bylines(), [{"name": "곽경민 한경닷컴 연예이슈팀 기자"}])
        self.assertEqual(byline.BylineAnalyzer("한경닷컴 산업경제팀 open@hankyung.com").get_bylines(), [{"name": "한경닷컴 산업경제팀", "email":"open@hankyung.com"}])

        self.assertEqual(byline.BylineAnalyzer("박상재 한경닷컴 기자 sangjae@hankyung.com").get_bylines(), [{"name": "박상재 한경닷컴 기자", "email":"sangjae@hankyung.com"}])
        self.assertEqual(byline.BylineAnalyzer("조문술 기자/freiheit@heraldcorp.com").get_bylines(), [{"name": "조문술 기자", "email":"freiheit@heraldcorp.com"}])
        self.assertEqual(byline.BylineAnalyzer("onlinenews@heraldcorp.com").get_bylines(), [{"email":"onlinenews@heraldcorp.com"}])

        self.assertEqual(byline.BylineAnalyzer("MBC뉴스 이준희입니다.", type=byline.BylineExtractor.TV).get_bylines(), [{"name": "이준희"}])
        self.assertEqual(byline.BylineAnalyzer("로스앤젤레스에서 MBC뉴스 이주훈입니다.", type=byline.BylineExtractor.TV).get_bylines(), [{"name": "이주훈"}])
        self.assertEqual(byline.BylineAnalyzer("못을 박은 적은 없습니다.YTN 김수진[suekim", type=byline.BylineExtractor.TV).get_bylines(), [{"name": "김수진", "email":"suekim"}])
        self.assertEqual(byline.BylineAnalyzer("분석했습니다.YTN 김상익입니다.", type=byline.BylineExtractor.TV).get_bylines(), [{"name": "김상익"}])

        #self.assertEqual(byline.BylineAnalyzer("").get_bylines(), [{"name": ""}])

    def test_files(self):
        for sample in byline_samples():
            print(sample["num"])
            san = ntrust.content.Sanitizer(sample["mediaId"])
            san.process(sample['contents'])
            #print(san.get_contents())
            #self.assertEqual(san.get_contents_lines(), sample['sanitized_lines'])
            self.assertEqual(san.get_bylines(), sample["bylines"])





if __name__ == '__main__':
    unittest.main()
