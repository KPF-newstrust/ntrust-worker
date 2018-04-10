import logging

from ..base import BaseSanitizer, BylineInEndOfLine


log = logging.getLogger('ntrust.sanitizer')


class Sanitizer(BylineInEndOfLine, BaseSanitizer):
    '''
    매일신문 ㅜㅜㅜ
    '''

    def _remove_by_email(self, lines):
        log.debug('check email address in the head')
        for n, i in enumerate(lines):
            m = self.RE_EMAIL_END_OF_LINE.search(i)
            if m is None:
                break

            log.debug('found email, `%s`', m.groups())
            lines[n] = ''
            break

        return lines
