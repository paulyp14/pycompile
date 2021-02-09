import re
from typing import Pattern

from pycompile.lex.token.token import Token


class Punctuation(Token):
    pattern: Pattern = re.compile('^(\{|\}|\(|\)|\[|\]|;|,|\.|::|:)')

    _NAME_MAP = {
        '{': 'opencubr',
        '}': 'closecubr',
        '(': 'openpar',
        ')': 'closepar',
        '[': 'opensqbr',
        ']': 'closesqbr',
        ';': 'semi',
        ',': 'comma',
        '.': 'dot',
        '::': 'coloncolon',
        ':': 'colon'
    }

    def __init__(self, code: str):
        lexm = Punctuation.pattern.match(code).group()
        super().__init__(lexm, Punctuation._NAME_MAP[lexm])

    @staticmethod
    def match(code: str) -> bool:
        return Punctuation.pattern.match(code) is not None
