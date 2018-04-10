import re
import logging

from ..base import BaseSanitizer, BylineInEndOfLine, remove_redundants, remove_gija_byline


log = logging.getLogger('ntrust.sanitizer')


class Sanitizer(BylineInEndOfLine, BaseSanitizer):
    '''
    중부매일 ㅜㅜㅜ
    '''

    RE_REDUNDANTS = (
        re.compile('^[\s]*[\w][\w]*[\s]*\/[\s]*[\w][\w]*[\s]*$'),
    )

    RE_GIJA_BYLINE = re.compile('[\s]*\/[\s][\s]*[\w][\w]*$')

    def _remove(self, lines=None):
        if lines is None:
            lines = self.content.strip().split('\n')

        lines = remove_redundants(lines, self.RE_REDUNDANTS)
        lines = remove_gija_byline(lines, pattern=self.RE_GIJA_BYLINE)

        return super(Sanitizer, self)._remove(lines)
