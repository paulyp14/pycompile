"""

"""
from typing import List, Union
from pycompile.lex.token import *


class LexicalAnalyzer:

    precedence: List[Token] = [Comment, Operator, Punctuation, Reserved, Id, Float, Integer, String]

    def __init__(self):
        self.tokens: List[Token] = []
        self.code: Union[None, str] = None

    def tokenize(self, code: str):
        self.code = code
        while len(code) > 0:
            code = self.extract_token(code)

    def tokens(self):
        return self.tokens

    def extract_token(self, code: str) -> str:
        token = LexicalAnalyzer.next_token(code)
        self.tokens.append(token)
        return token.replace_self(code.lstrip())

    @staticmethod
    def next_token(code: str) -> Token:
        code = code.lstrip()
        for token_class in LexicalAnalyzer.precedence:
            if token_class.match(code):
                return token_class(code)
