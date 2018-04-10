import re
import logging

from ..base import BaseSanitizer, BylineInEndOfLine, remove_redundants


log = logging.getLogger('ntrust.sanitizer')


class Sanitizer(BylineInEndOfLine, BaseSanitizer):
    '''
    아시아투데이 디지털뉴스팀 ㅜㅜㅜ
    '''

    RE_REDUNDANTS_HEAD = (
        re.compile('^[\s]*아시아투데이 디지털뉴스팀 =[\s]*'),
    )

    RE_REDUNDANTS_TAIL = (
        re.compile('^[\s]*\[.*\][\s]*$'),
        re.compile('[\s]*\[아시아투데이.*\][\s]*$'),
    )

    def _remove(self, lines=None):
        if lines is None:
            lines = self.content.strip().split('\n')

        lines = remove_redundants(lines, self.RE_REDUNDANTS_HEAD, reverse=False, line_based=False)
        lines = remove_redundants(lines, self.RE_REDUNDANTS_TAIL, reverse=True, line_based=False)

        return super(Sanitizer, self)._remove(lines)
