import re
from typing import Pattern

from pycompile.lex.token.token import Token


class Integer(Token):
    # pattern to match an integer
    # do not include negative lookaheads because those are encoding special cases
    pattern: Pattern = re.compile('^([1-9][0-9]*|0)')

    def __init__(self, code: str):
        super().__init__(Integer.pattern.match(code).group(), 'intnum')

    @staticmethod
    def match(code: str) -> bool:
        return Integer.pattern.match(code) is not None
