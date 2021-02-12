"""

"""
import re
from typing import List, Union, Tuple, Pattern
from pycompile.lex.token import *


class LexicalAnalyzer:

    precedence: List[Token] = [Comment, Operator, Punctuation, Reserved, Id, Float, Integer, String]
    whitespace: Pattern = re.compile('\s')

    def __init__(self):
        self.tokens: List[Token] = []
        self.code: Union[None, str] = None
        self.tokenized: Union[None, str] = None
        self.num_lines: int = 0

    def tokenize(self, raw_code: str):
        # set the info for the tokenization
        self.code = raw_code
        self.num_lines = len(self.code.split('\n'))
        self.tokenized = ''
        # start the tokenization
        line, start_idx = 1, 0
        # tokenize until there are no tokens left
        while len(raw_code) > 0:
            # extract one token
            raw_code, tok_start, tok_end = self.extract_token(raw_code)
            # count the number of lines between this token and the last token and use it to set the position
            line += self.code[start_idx: start_idx + tok_start].count('\n')
            self.tokens[-1].set_position(line)
            # if this was a comment and it was multiline, add the numbers of lines now
            # so the next token has the right position
            line += 0 if not isinstance(self.tokens[-1], Comment) else self.tokens[-1].get_num_lines()
            # add the string representation of the token to the tokenized code
            self.tokenized += (
                self.code[start_idx: start_idx + tok_start] +
                (self.tokens[-1].tok_str() if not self.tokens[-1].was_inserted() else '')
            )
            # set the end as the new start
            start_idx += tok_end

    def extract_token(self, current_code: str) -> Tuple[str, int, int]:
        token = LexicalAnalyzer.next_token(current_code)
        if token is not None:
            self.tokens.append(token)
        stripped_code = current_code.lstrip()
        start_idx = len(current_code) - len(stripped_code)
        end_idx = start_idx + (len(token) if token is not None else len(current_code))

        return token.replace_self(stripped_code) if token is not None else '', start_idx, end_idx

    def write_tokenized(self, token_file: str):
        with open(token_file, 'w') as f:
            f.write(self.tokenized)

    def write_errors(self, error_file: str):
        with open(error_file, 'w') as f:
            lines = [
                token.formatted_str()
                for token in self.tokens
                if isinstance(token, Invalid)
            ]
            f.write('\n'.join(lines))

    @staticmethod
    def next_token(code: str) -> Union[Token, None]:
        code = code.lstrip()
        token = LexicalAnalyzer.find_match(code)
        if token is not None:
            # valid token, return
            return token
        # no match found, have to create an invalid token
        if len(code) == 0:
            return None
        elif code[0] == '"' and len(code) > 1:
            # there is an invalid string
            idx = code[1:].find('"')
            idx = idx + 2 if idx != -1 else len(code)
        else:
            # there is something else invalid
            whitespace_match = LexicalAnalyzer.whitespace.search(code)
            # =====
            # breaking invalid lexemes only on whitespace
            # idx = len(code) if not whitespace_match else whitespace_match.start()

            # =====
            # breaking invalid lexemes on the next valid
            whitespace_idx = len(code) if not whitespace_match else whitespace_match.start()
            next_tok_idx = whitespace_idx
            for i in range(1, len(code)):
                if LexicalAnalyzer.find_match(code[i:].lstrip()) is not None:
                    next_tok_idx = i
                    break
            idx = next_tok_idx if next_tok_idx < whitespace_idx else whitespace_idx
        return Invalid(code[:idx])

    @staticmethod
    def find_match(code: str) -> Union[Token, None]:
        for token_class in LexicalAnalyzer.precedence:
            if token_class.match(code):
                return token_class(code)
        return None
