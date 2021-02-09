import re
from typing import Pattern

from pycompile.lex.token.token import Token


class Operator(Token):
    pattern: Pattern = re.compile('^(==|<>|<=|>=|<|>|\+|-|\*|/|=|\||&|!|\?)')

    _NAME_MAP = {
        '==': 'eq',
        '<>': 'noteq',
        '<=': 'leq',
        '>=': 'geq',
        '<': 'lt',
        '>': 'gt',
        '+': 'plus',
        '-': 'minus',
        '*': 'mult',
        '/': 'div',
        '=': 'assign',
        '|': 'or',
        '!': 'not',
        '&': 'and',
        '?': 'qmark'
    }

    def __init__(self, code: str):
        lexm = Operator.pattern.match(code).group()
        super().__init__(lexm, Operator._NAME_MAP[lexm])

    @staticmethod
    def match(code: str) -> bool:
        return Operator.pattern.match(code) is not None
