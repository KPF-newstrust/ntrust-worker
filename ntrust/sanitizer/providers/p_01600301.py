import re

from ..base import BaseSanitizer, BylineInEndOfLine, remove_redundants


class Sanitizer(BylineInEndOfLine, BaseSanitizer):
    RE_GIJA = [
        re.compile('([\w][\w]*[\s]*기자[\s]*[\w][\w]*@.*)'),
        re.compile('^\/([\w][\w\s]*)'),
        re.compile('([\s]*[\w][\w]*@.*)'),
    ] + list(BylineInEndOfLine.RE_GIJA)

    RE_REDUNDANTS = (
        re.compile('^[\s]*※[\s]*이[\s]*기사는[\s]*지역신문발전위원회[\s]*취재[\s]*지원으로[\s]*작성됐습니다.[\s]*$'),
    )

    def _remove_by_broken_email(self, lines):
        return lines

    def _get_byline(self):
        return self.byline

    def _remove(self, lines=None):
        if lines is None:
            lines = self.content.strip().split('\n')

        lines = remove_redundants(lines, self.RE_REDUNDANTS, reverse=True)

        return super(Sanitizer, self)._remove(lines)
