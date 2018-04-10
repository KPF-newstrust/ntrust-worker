import re
import logging

from ..base import BaseSanitizer, BylineInEndOfLine, remove_related_articles, remove_redundants, remove_gija_byline


log = logging.getLogger('ntrust.sanitizer')


class Sanitizer(BylineInEndOfLine, BaseSanitizer):
    '''
    국민일보 ㅜㅜㅜ
    '''

    ITEM_CHARS = (
        '☞',
        '▶',
    )

    RE_REDUNDANTS = (
        re.compile('^[\s]*\[.*\][\s]*$'),
    )

    RE_BYLINE = re.compile('(.*)[\s]*기자[\s]+')

    def _remove(self, lines=None):
        if lines is None:
            lines = self.content.strip().split('\n')

        lines = remove_related_articles(lines, self.ITEM_CHARS)
        lines = remove_redundants(lines, self.RE_REDUNDANTS)

        lines = super(Sanitizer, self)._remove(lines)
        lines = remove_gija_byline(lines, pattern=self.RE_BYLINE)

        return lines

    def _get_byline(self):
        return self.byline
