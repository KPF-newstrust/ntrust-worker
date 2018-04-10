import re
import logging

from ..base import BaseSanitizer, BylineInEndOfLine, remove_related_articles, remove_gija_byline, remove_macros


log = logging.getLogger('ntrust.sanitizer')


class Sanitizer(BylineInEndOfLine, BaseSanitizer):
    '''
    경인일보 ㅜㅜㅜ
    '''

    ITEM_CHARS = (
        '※',
    )

    RE_REDUNDANTS = (
        re.compile('^[\s]*\[.*\][\s]*$'),
    )

    RE_BYLINE = re.compile('^\/[\s]*')

    RE_MACROS = (
        dict(
            s=re.compile('[\s]*(\[IMG[\d][\d]*\])[\s]*'),
            r=lambda x: re.compile(r'(\s*)(\[IMG[\d][\d]*\])(\s*)').sub(r'\1\3', x),
        ),
    )

    def _remove(self, lines=None):
        if lines is None:
            lines = self.content.strip().split('\n')

        lines = remove_related_articles(lines, self.ITEM_CHARS)
        lines = remove_gija_byline(lines, pattern=self.RE_BYLINE)
        lines = remove_macros(lines, patterns=self.RE_MACROS)

        return super(Sanitizer, self)._remove(lines)
