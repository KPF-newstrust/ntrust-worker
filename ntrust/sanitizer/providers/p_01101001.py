import re
import logging

from ..base import BaseSanitizer, BylineInEndOfLine


log = logging.getLogger('ntrust.sanitizer')


class Sanitizer(BylineInEndOfLine, BaseSanitizer):
    '''
    한겨례 ㅜㅜㅜ
    '''
    RE_LIST_ITEM = re.compile('^([■▶][\s]*).*')

    def _remove(self, lines=None):
        if lines is None:
            lines = self.content.strip().split('\n')

        lines = self.remove_related_articles(lines)
        lines = self.remove_redundants(lines)

        return super(Sanitizer, self)._remove(lines)

    def remove_related_articles(self, lines):
        for n, i in enumerate(lines[::-1]):
            if not i.strip():
                continue

            m = self.RE_LIST_ITEM.search(i.strip())
            if m is None:
                break

            lines[len(lines) - (n + 1)] = ''

        if n < 1:
            log.debug('related article not found.')

        return lines if n < 1 else lines[:-1 * n]

    RE_REDUNDANTS = (
        re.compile('^한겨레[\s]*그림판[\s]*보러가기'),
    )

    def remove_redundants(self, lines):
        for n, i in enumerate(lines[::-1]):
            if not i.strip():
                continue

            m = list(filter(lambda x: x.search(i) is not None, self.RE_REDUNDANTS))
            if not m:
                break

            log.debug('redundant found, `%s`' % i)
            lines[len(lines) - (n + 1)] = ''

        if n < 1:
            log.debug('redundants not found.')

        return lines if n < 1 else lines[:-1 * n]
