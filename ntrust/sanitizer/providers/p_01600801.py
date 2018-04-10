import re

from ..base import BaseSanitizer, BylineInEndOfLine


class Sanitizer(BylineInEndOfLine, BaseSanitizer):
    RE_GIJA = [
        # added for `01600801-01600801.20160606000412577-source.txt`
        re.compile('([\w\s\(\)\=][\w\s\(\)\=]*[\s]+(기자|위원|특파원))[\s·]*(\/||)[\s·]*'),
        re.compile('([\w][\w]*(기자|위원|특파원))[\s·]*(\/||)[\s·]*'),
    ] + list(BylineInEndOfLine.RE_GIJA)

    def _get_byline(self):
        return self.byline
