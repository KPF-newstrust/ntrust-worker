import unittest

from ntrust import textcount

class TestTextCount(unittest.TestCase):

    def test_txtlen(self):
        self.assertEqual(textcount.length(" ABC "), 3)
        self.assertEqual(textcount.length("한A글"), 3)
        self.assertEqual(textcount.length("  "), 0)
        self.assertEqual(textcount.length("  A  "), 1)
        self.assertEqual(textcount.length("  A    B  한    C"), 7)
        self.assertEqual(textcount.length("한글은한글자"), 6)
        self.assertEqual(textcount.length("엔터도\n한글자"), 7)
        self.assertEqual(textcount.length("엔터도\n\n\n한글자"), 7)
        self.assertEqual(textcount.length("끝\n\n\n\n\n"), 1)
        self.assertEqual(textcount.length("\n\n\n\n\n시작"), 2)

    def test_mark_counter(self):
        self.assertEqual(textcount.number_of_question_marks("없어"), 0)
        self.assertEqual(textcount.number_of_question_marks("없어?"), 1)
        self.assertEqual(textcount.number_of_question_marks("?있어?"), 2)
        self.assertEqual(textcount.number_of_question_marks("? ???"), 4)
        self.assertEqual(textcount.number_of_exclamation_marks("없어"), 0)
        self.assertEqual(textcount.number_of_exclamation_marks("없어!"), 1)
        self.assertEqual(textcount.number_of_exclamation_marks("!있어!"), 2)
        self.assertEqual(textcount.number_of_exclamation_marks("!!! !! ! !"), 7)
        self.assertEqual(textcount.number_of_exclamation_marks("!있어!"), 2)

        self.assertEqual(textcount.number_of_white_spaces("\n\n\n\n\n헐\n\n"), 0)
        self.assertEqual(textcount.number_of_white_spaces("A B C D"), 3)
        self.assertEqual(textcount.number_of_white_spaces("A  B \tC\t\tD"), 3)
        self.assertEqual(textcount.number_of_white_spaces("A \u2028 B \u2029\tC\t\tD"), 3)
        self.assertEqual(textcount.number_of_white_spaces("확립된 관례"), 1)
        self.assertEqual(textcount.number_of_white_spaces("조용한 아침의 나라"), 2)

        # FIXME: 따옴표 갯수 검사 로직이 이게 아닐텐데..
        self.assertEqual(textcount.number_of_singlequote_marks("I'm a boy"), 1)
        self.assertEqual(textcount.number_of_singlequote_marks("--'ouch'--"), 2)
        self.assertEqual(textcount.number_of_singlequote_marks("''''"), 4)
        self.assertEqual(textcount.number_of_singlequote_marks("aa 'bb' cc 'dd'"), 4)
        self.assertEqual(textcount.number_of_doublequote_marks('가나다"라마바'), 1)
        self.assertEqual(textcount.number_of_doublequote_marks('가나다"라"마바'), 2)
        self.assertEqual(textcount.number_of_doublequote_marks('가나다""라""마바'), 4)


    def test_title_special_word(self):
        self.assertEqual(textcount.is_title_shock_ohmy("충격,이럴수가"), True)
        self.assertEqual(textcount.is_title_shock_ohmy("충격,이 럴수가"), False)
        self.assertEqual(textcount.is_title_shock_ohmy("충격, 이럴 수가"), True)
        self.assertEqual(textcount.is_title_shock_ohmy("충격이럴수가"), False)
        self.assertEqual(textcount.is_title_exclusive_news("단독"), True)
        self.assertEqual(textcount.is_title_exclusive_news("[단독"), True)
        self.assertEqual(textcount.is_title_exclusive_news("[단독보도"), True)
        self.assertEqual(textcount.is_title_exclusive_news("제목에 그냥 단독이 쓰임"), False)
        self.assertEqual(textcount.is_title_breaking_news("속보"), True)
        self.assertEqual(textcount.is_title_breaking_news("[속보]"), True)
        self.assertEqual(textcount.is_title_breaking_news("[긴급속보]"), True)
        self.assertEqual(textcount.is_title_breaking_news("뒤쪽에 속보가 오면 패스"), False)
        self.assertEqual(textcount.is_title_plan_news("기획"), True)
        self.assertEqual(textcount.is_title_plan_news("[기획"), True)
        self.assertEqual(textcount.is_title_plan_news("기획기사"), True)
        self.assertEqual(textcount.is_title_plan_news("신년기획특집"), True)
        self.assertEqual(textcount.is_title_plan_news("제목을 기획하다"), False)

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

if __name__ == '__main__':
    unittest.main()
