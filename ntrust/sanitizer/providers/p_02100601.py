import re

from ..base import BaseSanitizer, BylineInEndOfLine, remove_redundants, split_sentence


RE_MULTIPLE_NEW_LINE = re.compile('[\n][\n][\n]*')


class Sanitizer(BylineInEndOfLine, BaseSanitizer):
    '''
    한국경제
    '''
    RE_REDUNDANTS_HEAD = (
        re.compile('^[\s]*\[.*\][\s]*'),  # mostly it's byline
    )

    RE_REDUNDANTS = (
        re.compile('(한경\+)'),
        re.compile('(무단[\s]*전재.*$)'),
        re.compile('(재배포[\s]*금지.*$)'),
        re.compile('(구독신청.*$)'),
        re.compile('(기사제보 및 보도자료.*$)'),
    )
    RE_REDUNDANTS_LINE = (
        re.compile('(한경닷컴[\s]*뉴스룸)$'),
    )
    RE_USELESS_EMAILS = (
        re.compile('(한경닷컴[\s]*뉴스룸[\s]*[a-zA-Z0-9_.+-]+@hankyung.com)'),
    )

    def _remove_by_broken_email(self, lines):
        for n, i in enumerate(lines[::-1]):
            if not i.strip():
                continue

            m = list(filter(lambda x: x.search(i) is not None, self.RE_USELESS_EMAILS))
            if len(m) < 1:
                break

            for j in m:
                i = j.sub('', i)

            lines[len(lines) - (n + 1)] = i

        return lines

    def _get_byline(self):
        return self.byline

    def _remove(self, lines=None):
        if lines is None:
            lines = self.content.strip().split('\n')

        lines = remove_redundants(lines, self.RE_REDUNDANTS_HEAD, reverse=False, line_based=False)

        # multiple line will be considered as line-break
        content = RE_MULTIPLE_NEW_LINE.sub('@@@@@', '\n'.join(lines))
        lines = remove_redundants(
            split_sentence(content.replace('\n', '').replace('@@@@@', '\n\n')),
            self.RE_REDUNDANTS,
            reverse=True,
            line_based=False,
        )
        lines = remove_redundants(lines, self.RE_REDUNDANTS_LINE, reverse=True, line_based=True)

        return super(Sanitizer, self)._remove(lines)
