import re
import logging

from ..base import BaseSanitizer, BylineInEndOfLine, remove_redundants


log = logging.getLogger('ntrust.sanitizer')


class Sanitizer(BylineInEndOfLine, BaseSanitizer):
    '''
    매일경제 ㅜㅜㅜ
    '''

    RE_REDUNDANTS_HEAD = (
        re.compile('^[\s]*\[.*\][\s]*$'),
    )

    RE_REDUNDANTS_HEAD_PREFIX = (
        re.compile('^([\s]*\[[\s]*.*기자[\s]*\][\s]+)'),
    )

    RE_REDUNDANTS_TAIL = (
        re.compile('^[\s]*\[.*\][\s]*$'),
        re.compile('^([\s]*.*\:.*[\s]*)$'),
    )

    def _remove(self, lines=None):
        if lines is None:
            lines = self.content.strip().split('\n')

        lines = remove_redundants(lines, self.RE_REDUNDANTS_HEAD, reverse=False)
        lines = remove_redundants(lines, self.RE_REDUNDANTS_HEAD_PREFIX, reverse=False, line_based=False)
        lines = remove_redundants(lines, self.RE_REDUNDANTS_TAIL)

        return super(Sanitizer, self)._remove(lines)
