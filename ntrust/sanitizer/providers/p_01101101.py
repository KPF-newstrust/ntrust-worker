import re

from ..base import BaseSanitizer, BylineInEndOfLine, remove_redundants


class Sanitizer(BylineInEndOfLine, BaseSanitizer):
    def _get_byline(self):
        return self.byline

    RE_REDUNDANTS_HEAD = (
        re.compile('^[\s]*\[.*\][\s]*'),  # mostly it's byline
    )

    def _remove(self, lines=None):
        if lines is None:
            lines = self.content.strip().split('\n')

        lines = remove_redundants(lines, self.RE_REDUNDANTS_HEAD, reverse=False, line_based=False)

        return super(Sanitizer, self)._remove(lines)
