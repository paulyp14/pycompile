import re
from typing import Pattern

from pycompile.lex.token.token import Token


class Id(Token):
    pattern: Pattern = re.compile('^[a-zA-Z][a-zA-Z0-9_]*')

    def __init__(self, code: str):
        super().__init__(Id.pattern.match(code).group())

    @staticmethod
    def match(code: str) -> bool:
        return Id.pattern.match(code) is not None
