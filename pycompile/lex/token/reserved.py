import re
from typing import Pattern

from pycompile.lex.token.token import Token


class Reserved(Token):
    pattern: Pattern = re.compile('^(if|then|else|integer|float|string|void|public|private|func|var|class|while|read|write|return|main|inherits|break|continue)')

    def __init__(self, code: str):
        super().__init__(Reserved.pattern.match(code).group())

    @staticmethod
    def match(code: str) -> bool:
        return Reserved.pattern.match(code) is not None
