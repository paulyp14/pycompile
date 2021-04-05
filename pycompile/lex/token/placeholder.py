from pycompile.lex.token.token import Token


class Placeholder(Token):
    def __init__(self, code: str):
        super().__init__('Placeholder', 'Placeholder')