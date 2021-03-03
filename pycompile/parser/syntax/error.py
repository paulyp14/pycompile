from typing import Dict, List

from pycompile.lex.token import *


class SyntaxParsingError(Exception):

    _reverse_lookup: Dict = {
        Id: 'Id',
        Integer: 'Integer',
        Float: 'Float',
        String: 'String'
    }

    def __init__(self, token: Token, first_set: List, follow_set: List):
        super().__init__(self.create_message(token, first_set, follow_set))

    @staticmethod
    def create_message(token: Token, first_set: List, follow_set: List):
        msg = "Unexpected token '{}' at {}. Expected one of: {}"
        expected_list = [
            SyntaxParsingError.get_repr(item) for item in
            first_set if not (isinstance(item, str) and item == 'EPSILON')
        ]
        if 'EPSILON' in first_set:
            expected_list += [SyntaxParsingError.get_repr(item) for item in follow_set]
        expected = ', '.join(expected_list)
        return msg.format(token.lexeme, token.position, expected)

    @staticmethod
    def get_repr(item):
        if isinstance(item, str):
            return item
        elif isinstance(item, Token):
            return item.lexeme
        else:
            return SyntaxParsingError._reverse_lookup[item]
