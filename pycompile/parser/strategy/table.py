from typing import Union

from pycompile.lex.token import *
from pycompile.utils.stack import Stack
from pycompile.parser.strategy.helper import Table
from pycompile.parser.strategy.strategy import ParsingStrategy


class TableParser(ParsingStrategy):

    def __init__(self, code: str = None, table: Table = None):
        super().__init__(code)
        self.table: Table = table
        self.symbol_stack: Stack = Stack()
        self.encountered_error: bool = False

    def _parse(self):
        self.push(Final())
        self.push('START')
        cur_tok = self.next_token()
        while not isinstance(self.symbol_stack.peek(), Final):
            cur_sym = self.symbol_stack.peek()
            if self.is_terminal(cur_sym):
                # terminal symbol
                if self.terminal_match(cur_sym, cur_tok):
                    # we have a match
                    self.pop()
                    cur_tok = self.next_token()
                else:
                    self.__found_error()
            else:
                # non-terminal
                if self.non_terminal_match(cur_sym, cur_tok):
                    self.pop()
                    self.inverse_push(cur_tok, cur_sym)
                else:
                    self.__found_error()
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

    def __found_error(self):
        self.skip_errors()
        if not self.encountered_error:
            self.encountered_error = True

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

    def skip_errors(self):
        pass
