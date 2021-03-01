from pycompile.lex.token.token import Token


class Final(Token):

    def __init__(self):
        super().__init__("$", "END")
