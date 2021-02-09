import re
from typing import Pattern

from pycompile.lex.token.token import Token


class Invalid(Token):

    num_pattern: Pattern = re.compile('[0-9]')

    def __init__(self, code: str):
        # classify the problem
        if len(code) == 1:
            name = 'invalidchar'
            self.proper_name = 'character'
        elif code[0] == '"':
            name = 'invalidstringlit'
            self.proper_name = 'string'
        elif Invalid.num_pattern.match(code[0]):
            name = 'invalidnum'
            self.proper_name = 'number'
        else:
            name = 'invalidid'
            self.proper_name = 'identifier'

        super().__init__(code, name)

    def formatted_str(self):
        return f'Lexical error: Invalid {self.proper_name}: "{self.lexeme}": line {self.position}'
