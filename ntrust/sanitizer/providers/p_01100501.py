import re
import logging

from ..base import BaseSanitizer, BylineInEndOfLine, remove_redundants


log = logging.getLogger('ntrust.sanitizer')


class Sanitizer(BylineInEndOfLine, BaseSanitizer):
    '''
    문화일보 ㅜㅜㅜ
    '''

    RE_REDUNDANTS = (
        re.compile('^[\s]*\[.*\][\s]*$'),
        re.compile('^[\s]*포커스뉴스[\s]*$'),
    )

    def _remove(self, lines=None):
        if lines is None:
            lines = self.content.strip().split('\n')

        lines = remove_redundants(lines, self.RE_REDUNDANTS)

        return super(Sanitizer, self)._remove(lines)
