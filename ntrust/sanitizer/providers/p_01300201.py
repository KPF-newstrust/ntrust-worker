from ..base import BaseSanitizer, BylineInEndOfLine


class Sanitizer(BylineInEndOfLine, BaseSanitizer):
    def _remove_by_broken_email(self, lines):
        return lines

    def _get_byline(self):
        return self.byline
