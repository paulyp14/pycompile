import re
from typing import Pattern

from pycompile.lex.token.token import Token


class Float(Token):
    # pattern to match a float with optional e[+ -][1-9][0-9]*
    # do not include negative lookaheads because those are encoding special cases
    pattern: Pattern = re.compile('^(([1-9][0-9]*)|0)\.(([0-9]*[1-9])|0)(e[\+\-]?([1-9][0-9]*|0))?')

    def __init__(self, code: str):
        super().__init__(Float.pattern.match(code).group(), 'floatnum')

    @staticmethod
    def match(code: str) -> bool:
        return Float.pattern.match(code) is not None
