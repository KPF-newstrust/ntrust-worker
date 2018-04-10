import unittest

from ntrust import sentences

class TestQuotedSentenceExtract(unittest.TestCase):

    def test_quote(self):
        self.assertEqual(sentences.extract_quoted(" A'B'C "), ["B"])
        self.assertEqual(sentences.extract_quoted(' A"안녕하세요"C '), ["안녕하세요"])

        self.assertEqual(sentences.extract_quoted("더불어민주당은 20대 국회 개원에 발 맞춰 회의장 배경판을 파란색 원 123개와 ''살피는 민생, 지키는 안보 20대 국회를 시작합니다''라는 글로 바뀌었다."), ["살피는 민생, 지키는 안보 20대 국회를 시작합니다"])
        self.assertEqual(sentences.extract_quoted("이날 비상대책위 회의에서 “새누리당이 어제부터 국회의장직을 가져가겠다고 입장을 선회했다”며 “(이대로는) 정상적인 협상이 어렵다”고 비판했다."), ["새누리당이 어제부터 국회의장직을 가져가겠다고 입장을 선회했다", "(이대로는) 정상적인 협상이 어렵다"])
        self.assertEqual(sentences.extract_quoted("""원내수석부대표는 “정 여당에서 의장을 못 내놓겠다면, 국회법에 따르면 무기명 자유투표를 하기로 돼 있기 때문에 그렇게 하는 방법밖에 없다”며 수적 우위를 앞세운 자유투표를 재차 주장했다."""), ["정 여당에서 의장을 못 내놓겠다면, 국회법에 따르면 무기명 자유투표를 하기로 돼 있기 때문에 그렇게 하는 방법밖에 없다"])
        self.assertEqual(sentences.extract_quoted("""이에 대해 제1당이 아닌 여당 출신이 국회의장을 맡는 게 ‘확립된 관례’라며 반발하고 있다."""), ['확립된 관례'])
        #self.assertEqual(sentences.extract_quoted("""원내대표는 “국회의장은 여당이 하는 게 관례이지, 야당 주장처럼 1당이 하는 관례는 없었다”며 “한 번 정도의 예외를 제외하면 여당이 하는 게 확립된 관례인데 야당이 이걸 깨려고 하는 것”이라고 비판했다."""), ['국회의장은 여당이 하는 게 관례이지, 야당 주장처럼 1당이 하는 관례는 없었다','한 번 정도의 예외를 제외하면 여당이 하는 게 확립된 관례인데 야당이 이걸 깨려고 하는 것'])
        #self.assertEqual(sentences.extract_quoted("""의원은 “야당이 (의장을) 한다고 봤을 때 결국 박근혜정부의 잔여 임기는 식물국회에 식물정부, 무능한 정부로 전락할 가능성이 크다”며 ‘의장직 절대사수’를 주장했다."""),['야당이 (의장을) 한다고 봤을 때 결국 박근혜정부의 잔여 임기는 식물국회에 식물정부, 무능한 정부로 전락할 가능성이 크다','의장직 절대사수'])

        self.assertEqual(sentences.get_text_front_quote("XXX.ABC DEF '안녕하세요'C ", "안녕하세요"), "ABC DEF")

if __name__ == '__main__':
    unittest.main()
