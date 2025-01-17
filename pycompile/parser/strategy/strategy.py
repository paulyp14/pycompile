from abc import ABC, abstractmethod
from typing import List, Tuple, Union

from pycompile.lex.token import Token
from pycompile.lex.analyzer import LexicalAnalyzer
from pycompile.parser.syntax.ast import AbstractSyntaxNode
from pycompile.parser.syntax.error import SyntaxParsingError


class ParsingStrategy(ABC):

    def __init__(self, code: str = None):
        self.code = code
        self.analyzer: LexicalAnalyzer = LexicalAnalyzer()
        self.current_token_idx: int = -1
        self.current_token: Union[Token, None] = None
        self.lookahead: Union[Token, None] = None
        self.success: bool = False
        self.rules: List[str] = []
        self.derivation: List[str] = []
        self.errors: List[SyntaxParsingError] = []
        self.ast: Union[AbstractSyntaxNode, None] = None

    def reset(self, code: str):
        self.code = code

    def parse(self, code: str = None) -> Tuple[bool, AbstractSyntaxNode, List[str], List[str]]:
        if code is not None:
            self.reset(code)
        if self.code is None:
            raise ValueError("No codegenr to parse")
        # tokenize and parse
        self.analyzer.tokenize(self.code)
        self.analyzer.add_final_token()
        self.analyzer.remove_comments()
        self._parse()
        return self.success, self.ast, self.rules, self.derivation

    @abstractmethod
    def _parse(self):
        ...

    def move(self):
        self.current_token_idx += 1
        self.current_token = self.analyzer.tokens[self.current_token_idx]
        if self.current_token_idx + 1 != len(self.analyzer):
            self.lookahead = self.analyzer.tokens[self.current_token_idx + 1]

    def next_token(self) -> Token:
        return self.analyzer.tokens[self.current_token_idx + 1]

    def set_lookahead(self):
        self.lookahead = self.next_token()

    def next(self) -> str:
        return self.lookahead.lexeme

