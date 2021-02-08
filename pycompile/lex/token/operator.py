import re
from typing import Pattern

from pycompile.lex.token.token import Token


class Operator(Token):
    pattern: Pattern = re.compile('^(==|<>|<=|>=|<|>|\+|-|\*|/|=|\||&|!|\?)')

    def __init__(self, code: str):
        super().__init__(Operator.pattern.match(code).group())

    @staticmethod
    def match(code: str) -> bool:
        return Operator.pattern.match(code) is not None
