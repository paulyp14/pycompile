"""
Token class represents lexical token generated by scanner
"""
import abc
from typing import Union


class Token(abc.ABC):

    def __init__(self, lexeme: str):
        self.lexeme: str = lexeme
        self.position = None

    def replace_self(self, code: str) -> str:
        return str.lstrip(code, self.lexeme)

    @staticmethod
    def match(code: str) -> bool:
        ...
