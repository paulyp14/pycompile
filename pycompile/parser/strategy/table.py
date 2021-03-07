from typing import Union

from pycompile.lex.token import *
from pycompile.utils.stack import Stack
from pycompile.parser.strategy.helper import Table
from pycompile.parser.strategy.strategy import ParsingStrategy
from pycompile.parser.syntax.error import SyntaxParsingError
from pycompile.parser.syntax.factory import AbstractSyntaxNodeFactory


class TableParser(ParsingStrategy):

    def __init__(self, code: str = None, table: Table = None):
        super().__init__(code)
        self.table: Table = table
        self.symbol_stack: Stack = Stack()
        self.semantic_stack: Stack = Stack()
        self.encountered_error: bool = False

    def _parse(self):
        self.push(Final())
        self.push('START')
        cur_tok = self.next_token()
        while not isinstance(self.symbol_stack.peek(), Final) and not isinstance(cur_tok, Final):
            cur_sym = self.symbol_stack.peek()
            if self.is_terminal(cur_sym):
                # terminal symbol
                if self.terminal_match(cur_sym, cur_tok):
                    # we have a match
                    self.pop()
                    cur_tok = self.next_token()
                else:
                    cur_tok = self.__found_error(cur_tok)
            elif self.is_semantic_action(cur_sym):
                self.process_semantic_action(cur_sym, cur_tok)
            else:
                # non-terminal
                if self.non_terminal_match(cur_sym, cur_tok):
                    self.pop()
                    self.inverse_push(cur_tok, cur_sym)
                else:
                    cur_tok = self.__found_error(cur_tok)
        if len(self.semantic_stack) > 0:
            self.ast = self.semantic_stack.pop()
        # all symbols
        if not isinstance(cur_tok, Final) or self.encountered_error:
            self.success = False
        else:
            self.success = True

    def push(self, item: Union[Token, str]):
        self.symbol_stack.push(item)
        self.rules.append(self.symbol_stack.contents())

    def pop(self):
        item = self.symbol_stack.pop()
        self.rules.append(self.symbol_stack.contents())
        return item

    def __found_error(self, token: Token) -> Token:
        token = self.skip_errors(token)
        if not self.encountered_error:
            self.encountered_error = True
        return token

    def inverse_push(self, token: Token, symbol: str):
        tokens = self.table.get(symbol, token)
        for i, token in enumerate(tokens[-1::-1]):
            if i + 1 == len(tokens):
                self.push(token)
            else:
                self.symbol_stack.push(token)

    def terminal_match(self,  cur_sym: str, cur_tok: Token) -> bool:
        return self.table.terminal_match(cur_sym, cur_tok)

    def non_terminal_match(self, cur_sym: str, cur_tok: Token) -> bool:
        if isinstance(cur_tok, (Float, Integer, String, Id)):
            using = type(cur_tok)
        else:
            using = cur_tok.lexeme
        return self.table.lookup(cur_sym, using) != 'Error'

    def is_terminal(self, symbol) -> bool:
        return self.table.is_terminal(symbol)

    def next_token(self) -> Token:
        next_tok = super().next_token()
        self.move()
        return next_tok

    def skip_errors(self, token: Token) -> Token:
        self.errors.append(SyntaxParsingError(
            token,
            self.table.get_first_for_symbol(self.symbol_stack.peek()),
            self.table.get_follow_for_symbol(self.symbol_stack.peek())
        ))
        if isinstance(token, Final) or self.table.in_first(self.symbol_stack.peek(), token):
            self.pop()
            if not isinstance(token, Final):
                token = self.next_token()
        else:
            breaker = True
            while breaker:
                if (
                    isinstance(token, Final) or
                    self.table.in_first(self.symbol_stack.peek(), token) or
                    (
                        self.table.epsilon_in_first(self.symbol_stack.peek()) and
                        self.table.in_follow(self.symbol_stack.peek(), token)
                    )
                ):
                    breaker = False
                    break
                # scan
                token = self.next_token()
        return token

    def is_semantic_action(self, cur_sym: Union[str, Token]) -> bool:
        return self.table.is_semantic_action(cur_sym)

    def process_semantic_action(self, cur_sym: str, token: Token):
        self.pop()
        # self.semantic_stack.push(cur_sym)
        # return
        node = AbstractSyntaxNodeFactory.create(
            cur_sym,
            token,
            self.analyzer.tokens[self.current_token_idx - 1],
            self.semantic_stack
        )
        self.semantic_stack.push(node)
