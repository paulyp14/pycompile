import re
from typing import Pattern

from pycompile.lex.token.token import Token


class Integer(Token):
    """
    _accepted_pattern is the integer pattern we are looking for
    first look for two negative lookaheads to not allow matches on:
        (?!([1-9][0-9]*|0)\.)
        an integer that starts a float that didn't match a float
        (?!(0[0-9]+))
        a multi-digit integer that starts with a zero
    look for a match on
        ([1-9][0-9]*|0)
        a number that starts with non-zero digit

    it is included as a static property of Float just for clarity/readability
    """
    _accepted_pattern: str = '([1-9][0-9]*|0)'
    # pattern: Pattern = re.compile('^(?!([1-9][0-9]*|0)\.)(?!(0[0-9]+))([1-9][0-9]*|0)')
    pattern: Pattern = re.compile('^([1-9][0-9]*|0)')

    def __init__(self, code: str):
        super().__init__(Integer.pattern.match(code).group(), 'intnum')

    @staticmethod
    def match(code: str) -> bool:
        return Integer.pattern.match(code) is not None
