import re
import logging

from ..base import BaseSanitizer, BylineInEndOfLine, remove_redundants


log = logging.getLogger('ntrust.sanitizer')


class Sanitizer(BylineInEndOfLine, BaseSanitizer):
    '''
    서울신문 ㅜㅜㅜ
    '''

    RE_REDUNDANTS_TAIL = (
        re.compile('^.*\=.*'),
    )

    def _remove(self, lines=None):
        if lines is None:
            lines = self.content.strip().split('\n')

        lines = super(Sanitizer, self)._remove(lines)
        lines = remove_redundants(lines, self.RE_REDUNDANTS_TAIL)

        return lines
