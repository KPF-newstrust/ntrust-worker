# -*- coding: utf-8 -*-

import re
import string
import logging
import importlib

from .constants import PROVIDER_CODE
from ..constants import SENTENCE_ENDING_CHARS, SRE_EMAIL
from ..util import clean_content, strip_html_entities
from ..sentences import split_sentence as split_sentence_by_tagger


log = logging.getLogger('ntrust.sanitizer')


_PUNCTUATIONS = ''.join(map(re.escape, string.punctuation))
_PUNCTUATIONS_WITHOUT_ENDING_CHARS = ''.join(map(re.escape, set(string.punctuation) - set(SENTENCE_ENDING_CHARS)))
_PUNCTUATIONS_WITHOUT_AT_SIGN = ''.join(map(re.escape, set(string.punctuation) - set(['@'])))
_PUNCTUATIONS_END_OF_LINE_AT_ARTICLE = '|'.join(map(re.escape, ['[', '][', ']']))

RE_PUNCTUATION_LINE = re.compile(
    '^[\s]*[%s][%s]*[\s]*$' % (_PUNCTUATIONS_WITHOUT_ENDING_CHARS, _PUNCTUATIONS_WITHOUT_ENDING_CHARS),
)
RE_PUNCTUATION_FIRST_IN_LINE = re.compile(
    '^([\s]*[%s][%s]*)' % (_PUNCTUATIONS, _PUNCTUATIONS),
)
RE_PUNCTUATION_END_OF_LINE_FOR_BYLINE = re.compile(
    '([\s]*[%s][%s]*)$' % (_PUNCTUATIONS_WITHOUT_AT_SIGN, _PUNCTUATIONS_WITHOUT_AT_SIGN),
)

RE_PUNCTUATION_END_OF_LINE_FOR_ARTICLE = re.compile(
    '([\s]*(%s)+)$' % (_PUNCTUATIONS_END_OF_LINE_AT_ARTICLE),
)
RE_MULTIPLE_NEW_LINE = re.compile('[\n][\n][\n][\n]*')
RE_SPACE = re.compile('([\s]+)')


def remove_punctuations(lines):
    if type(lines) in (str,):
        lines = lines.split('\n')

    nn = 0
    for n, i in enumerate(lines[::-1]):
        nn = n
        if not i.strip():
            continue

        if not RE_PUNCTUATION_LINE.search(i):
            break

    if nn > 0:
        lines = lines[:-1 * nn]

    return list(filter(lambda x: RE_PUNCTUATION_LINE.search(x) is None, lines))


RE_SENTENCE_ENDING_CHARS = re.compile('([\w!][%s]\s)' % ''.join(map(re.escape, SENTENCE_ENDING_CHARS)))


def split_sentence(s):
    return list(split_sentence_by_tagger(s))


def remove_related_articles(lines, item_chars=None):
    log.debug('check related articles')
    if item_chars is None:
        raise RuntimeError('`item_chars` must be given.')

    RE_LIST_ITEM = re.compile('^([%s][\s]*).*' % ''.join(map(re.escape, item_chars)))

    for n, i in enumerate(lines[::-1]):
        if not i.strip():
            continue

        m = RE_LIST_ITEM.search(i.strip())
        if m is None:
            break

        lines[len(lines) - (n + 1)] = ''

    if n < 1:
        log.debug('related article not found.')

    return lines


def remove_macros(lines, patterns=None):
    log.debug('check related articles')
    if patterns is None:
        raise RuntimeError('`patterns` must be given.')

    for n, i in enumerate(lines):
        for r in patterns:
            if r['s'].search(i) is None:
                continue

            log.debug('found pattern, %s', r)

            i = r['r'](i)

        lines[n] = i

    return lines


def remove_redundants(lines, patterns=None, reverse=True, line_based=True):
    if patterns is None:
        raise RuntimeError('`patterns` must be given.')

    if reverse:
        l = lines[::-1]
    else:
        l = lines

    log.debug('check redundants')
    for n, i in enumerate(l):
        if not i.strip():
            continue

        m = list(filter(lambda x: x.search(i) is not None, patterns))
        if not m:
            break

        if line_based:
            new_line = ''
        else:
            new_line = i
            for p in m:
                new_line = p.sub('', new_line)

        log.debug('redundant found, `%s`' % i)
        if reverse:
            idx = len(lines) - (n + 1)
        else:
            idx = n

        lines[idx] = new_line

    return lines


RE_BYLINE = re.compile('[\s]+\/(.*)기자[\s]*')


def remove_gija_byline(lines, pattern=None, reverse=True):
    if pattern is None:
        pattern = RE_BYLINE

    log.debug('remove byline')

    if reverse:
        l = lines[::-1]
    else:
        l = lines

    for n, i in enumerate(l):
        if not i.strip():
            continue

        m = pattern.search(i)
        if m is None:
            break

        log.debug('byline found, %d: `%s`' % (n, i))
        ss = split_sentence(i)

        if reverse:
            idx = len(lines) - (n + 1)
        else:
            idx = n

        lines[idx] = ' '.join(filter(lambda x: pattern.search(x) is None, ss))

    return lines


class Processor(object):
    def __init__(self, provider_code, default_provider_code=None):
        if provider_code not in PROVIDER_CODE:
            if default_provider_code is not None:
                provider_code = default_provider_code
            else:
                raise RuntimeError('unknown `provider_code` was given, `%s`', provider_code)

        try:
            self.m = importlib.import_module('.sanitizer.providers.p_{}'.format(provider_code), package='ntrust')
        except ImportError:
            log.debug('trying to import provider processor.')
            self.m = importlib.import_module('.sanitizer.providers.default', package='ntrust')

    def sanitize(self, content):
        content = clean_content(content, strip=True)
        content = strip_html_entities(content.strip())
        lines = remove_punctuations(content)
        lines = list(map(str.rstrip, lines))

        s = self.m.Sanitizer()
        lines = s.remove(lines)
        lines = list(map(str.rstrip, lines))
        lines = remove_punctuations(lines)

        content = RE_MULTIPLE_NEW_LINE.sub('\n\n', '\n'.join(lines).strip())

        return dict(
            content=content,
            byline=s.get_byline(),
        )


class BaseSanitizer(object):
    byline = None

    def __init__(self):
        pass

    def remove(self, lines=None):
        return self._remove(lines)

    def _remove(self, lines=None):
        raise NotImplemented

    def get_byline(self):
        b = self._get_byline()
        if b is None:
            return b

        b = sorted(b, reverse=True)

        return ' '.join(b).strip()

    def _get_byline(self):
        return None

    def check_byline(self, b):
        if len(RE_SPACE.findall(b)) > 4:
            return False

        return True

    def add_byline(self, b):
        if self.byline is None:
            self.byline = []

        if type(b) not in (str,):
            b = ' '.join(list(b))

        b = RE_PUNCTUATION_FIRST_IN_LINE.sub('', b.strip())
        b = RE_PUNCTUATION_END_OF_LINE_FOR_BYLINE.sub('', b.strip())
        self.byline.append(b)

        return


class BylineInEndOfLine(object):
    RE_EMAIL_END_OF_LINE = re.compile('[\s]*({})[\s]*$'.format(SRE_EMAIL))
    RE_GIJA = (
        re.compile('([\w\s\(\)\=\/][\w\s\(\)\=\/]*[\s]+(기자|위원|특파원|논설실장))[\s·]+'),
        # `·` was added for 01600301-01600301.20160608141220647-removed.txt
        re.compile('([\w][\w]*(기자|위원|특파원|논설실장))[\s·]+'),
    )
    RE_REPORTER = (
        re.compile('([\w][\w][\s\=\/]*[\w][\w]*[\s]*{}[\s]*)'.format(SRE_EMAIL)),
    )
    RE_NOT_BYLINE = (
        re.compile('[\s]*기사제보[\s]*'),
    )

    def _remove(self, lines=None):
        if lines is None:
            lines = self.content.strip().split('\n')

        for method in (
            self._remove_by_email,
            self._remove_by_broken_email,
            self._remove_gija,
            self._remove_reporter,
            self._remove_useless,
            # self._generate_method_remove_by_regex(self.RE_GIJA),
        ):
            lines = method(lines)

        return lines

    def _remove_by_email(self, lines):
        '''
        * If email address is found from the last line, it will be byline and removed.
        * If email pattern found in the line, split the line by the ending
            charaters(`.`, `?`, `!`) and remove the part, which contains the email pattern.
        '''

        def _0(x):
            if self.RE_EMAIL_END_OF_LINE.search(x) is not None and self.check_byline(x):
                return True

            return False

        def _1(x):
            if self.RE_EMAIL_END_OF_LINE.search(x) is None:
                return True

            if not self.check_byline(x):
                return True

            return False

        log.debug('check email')
        for n, i in enumerate(lines[::-1]):
            if not i.strip():
                continue

            m = self.RE_EMAIL_END_OF_LINE.search(i)
            if m is None:
                break

            log.debug('found email, `%s`', m.groups())

            ss = split_sentence(i)

            if len(list(filter(lambda x: x.search(i) is not None, self.RE_NOT_BYLINE))) < 1:
                self.add_byline(filter(_0, ss))

                lines[len(lines) - (n + 1)] = ' '.join(filter(_1, ss))

        return lines

    def _remove_by_broken_email(self, lines):
        log.debug('check broken email')
        for n, i in enumerate(lines[::-1]):
            if not i.strip():
                continue

            if '@' not in i:
                break

            log.debug('found broken email, `%s`', i)

            ss = split_sentence(i)
            lines[len(lines) - (n + 1)] = ' '.join(filter(lambda x: '@' not in x, ss))
            break

        return lines

    def _remove_gija(self, lines):
        log.debug('check gija')
        nn = -1

        def _0(r, x):
            if r.search(x + ' ') is not None and self.check_byline(x):
                return True

            return False

        def _1(r, x):
            if r.search(x + ' ') is None:
                return True

            if not self.check_byline(x):
                return True

            return False

        for n, i in enumerate(lines[::-1]):
            if not i.strip():
                continue

            if len(i.strip()) > 40:
                positions = list(map(
                    lambda y: y.search(i.strip() + ' ').span(),
                    filter(lambda x: x.search(i + ' '), self.RE_GIJA)
                ))
                if len(list(positions)) < 1:
                    break

                if (float(positions[-1][0]) / float(len(i.strip()))) < 0.7:
                    break

            m = list(filter(lambda x: x.search(i + ' '), self.RE_GIJA))
            if not m:
                continue

            nn = n
            log.debug('found gija, %d: `%s`', n, map(lambda x: x.search(i + ' ').groups(), m))

            ss = split_sentence(i)
            self.add_byline(filter(lambda y: list(filter(lambda x: _0(x, y), m)), ss))

            lines[len(lines) - (n + 1)] = ' '.join(filter(lambda y: list(filter(lambda x: _1(x, y), m)), ss))

        if nn < 0:
            log.debug('gija was not found.')

        return lines[:len(lines) - nn]

    def _remove_reporter(self, lines):
        log.debug('check reporter')
        nn = -1

        def _0(r, x):
            if r.search(x + ' ') is not None and self.check_byline(x):
                return True

            return False

        def _1(r, x):
            if r.search(x + ' ') is None:
                return True

            if not self.check_byline(x):
                return True

            return False

        for n, i in enumerate(lines[::-1]):
            if not i.strip():
                continue

            if len(i.strip()) > 40:
                positions = list(map(
                    lambda y: y.search(i.strip() + ' ').span(),
                    filter(lambda x: x.search(i + ' '), self.RE_REPORTER)
                ))
                if len(list(positions)) < 1:
                    break

                if (float(positions[-1][0]) / float(len(i.strip()))) < 0.7:
                    break

            m = list(filter(lambda x: x.search(i + ' '), self.RE_REPORTER))
            if not m:
                continue

            log.debug('found reporter, %d: `%s`', n, map(lambda x: x.search(i + ' ').groups(), m))
            nn = n

            ss = split_sentence(i)
            self.add_byline(filter(lambda y: list(filter(lambda x: _0(x, y), m)), ss))

            lines[len(lines) - (n + 1)] = ' '.join(filter(lambda y: list(filter(lambda x: _1(x, y), m)), ss))

        if nn < 0:
            log.debug('reporter was not found.')

        return lines[:len(lines) - nn]

    def _remove_useless(self, lines):
        for n, i in enumerate(lines[::-1]):
            if not i.strip():
                continue

            if not RE_PUNCTUATION_END_OF_LINE_FOR_ARTICLE.search(i):
                continue

            lines[len(lines) - (n + 1)] = RE_PUNCTUATION_END_OF_LINE_FOR_ARTICLE.sub('', i)
            break

        return lines

    def _generate_method_remove_by_regex(self, regex, help_string=None):
        if help_string is None:
            help_string = regex

        def w(lines):
            log.debug('check %s', help_string)
            m = regex.search(lines[-1])
            if m is None:
                log.debug('%s was not found.', help_string)
                return lines

            ss = split_sentence(lines[-1])
            if len(ss) < 2:
                lines = lines[:-1]
            else:
                lines[-1] = ' '.join(filter(lambda x: regex.search(x) is None, ss))

            log.debug('found `%s`', m.groups())

            return lines

        return w


def sanitize_title(s):
    s = clean_content(s, strip=True)
    s = s.replace('\n', ' ')
    s = strip_html_entities(s)

    return s
