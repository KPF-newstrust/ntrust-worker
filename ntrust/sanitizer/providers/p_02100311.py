import re
import logging

from ..base import BaseSanitizer, BylineInEndOfLine, remove_redundants, remove_gija_byline, remove_macros


log = logging.getLogger('ntrust.sanitizer')


class Sanitizer(BylineInEndOfLine, BaseSanitizer):
    '''
    서울경제 ㅜㅜㅜ
    '''

    RE_REDUNDANTS = (
        re.compile('^[\s]*\[.*\][\s]*$'),
    )

    RE_BYLINE = re.compile('[\s]*\/(.*)기자[\s]*')

    RE_MACROS = (
        dict(
            s=re.compile('[\s]*(\[[\w\s][\w\s]*\])[\s]*'),
            r=lambda x: '',
        ),
    )

    def _remove(self, lines=None):
        if lines is None:
            lines = self.content.strip().split('\n')

        lines = remove_redundants(lines, self.RE_REDUNDANTS)
        lines = remove_gija_byline(lines, pattern=self.RE_BYLINE)

        lines = remove_macros(lines, patterns=self.RE_MACROS)

        return super(Sanitizer, self)._remove(lines)
