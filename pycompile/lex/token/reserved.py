import re
from typing import Pattern

from pycompile.lex.token.token import Token


class Reserved(Token):
    pattern: Pattern = re.compile('^(if|then|else|integer|float|string|void|public|private|func|var|class|while|read|write|return|main|inherits|break|continue)')

    def __init__(self, code: str):
        # reserved keyword is both lexeme and name
        lexm = Reserved.pattern.match(code).group()
        super().__init__(lexm, lexm)

    @staticmethod
    def match(code: str) -> bool:
        return Reserved.pattern.match(code) is not None
