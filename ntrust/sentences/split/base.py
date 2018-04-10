SENTENCE_FLAG_SKIP = 'X'


class Sentence(str):
    def __new__(cls, v, flag=None):
        obj = str.__new__(cls, v)
        obj.flag = flag

        return obj

    def strip(self):
        return self.__class__(str(self).strip(), self.flag)
