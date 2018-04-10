import re
import logging

from ..base import BaseSanitizer, BylineInEndOfLine, remove_gija_byline


log = logging.getLogger('ntrust.sanitizer')


class Sanitizer(BylineInEndOfLine, BaseSanitizer):
    '''
    국제신문 ㅜㅜㅜ
    '''

    RE_BYLINE = re.compile('(.*)[\s]*기자[\s]*$')

    def _remove(self, lines=None):
        if lines is None:
            lines = self.content.strip().split('\n')

        lines = super(Sanitizer, self)._remove(lines)
        lines = remove_gija_byline(lines, pattern=self.RE_BYLINE)

        return lines
