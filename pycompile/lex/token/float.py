import re
from typing import Pattern

from pycompile.lex.token.token import Token


class Float(Token):
    """
    _accepted_pattern is the float pattern we are looking for
    it is included twice in Float.pattern:
        first it is included in the negative lookahead, where it is followed by 0+
            this excludes any float that has trailing 0s
        second it is included as the pattern to look for, so that floats without trailing 0s are matched

    it is included as a static property of Float just for clarity/readability
    """
    _accepted_pattern: str = '(([1-9][0-9]*)|0).(([0-9]*[1-9])|0)'
    pattern: Pattern = re.compile('(?!(([1-9][0-9]*)|0).(([0-9]*[1-9])|0)0+)^(([1-9][0-9]*)|0).(([0-9]*[1-9])|0)')

    def __init__(self, code: str):
        super().__init__(Float.pattern.match(code).group())

    @staticmethod
    def match(code: str) -> bool:
        return Float.pattern.match(code) is not None
