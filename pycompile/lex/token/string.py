import re
from typing import Pattern

from pycompile.lex.token.token import Token


class String(Token):
    pattern: Pattern = re.compile('^"[a-zA-Z0-9_ ]*"')

    def __init__(self, code: str):
        super().__init__(String.pattern.match(code).group(), 'stringlit')

    @staticmethod
    def match(code: str) -> bool:
        return String.pattern.match(code) is not None
