import re
import logging

from ..base import BaseSanitizer, BylineInEndOfLine, remove_gija_byline


log = logging.getLogger('ntrust.sanitizer')


class Sanitizer(BylineInEndOfLine, BaseSanitizer):
    '''
    충북일보 ㅜㅜㅜ
    '''

    RE_BYLINE = re.compile('[\s][\s]*/(.*)[\s]*기자[\s]*$')

    def _remove(self, lines=None):
        if lines is None:
            lines = self.content.strip().split('\n')

        lines = remove_gija_byline(lines, pattern=self.RE_BYLINE)

        return super(Sanitizer, self)._remove(lines)
