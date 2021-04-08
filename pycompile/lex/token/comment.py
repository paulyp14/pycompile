import re
from typing import Pattern

from pycompile.lex.token.token import Token


class Comment(Token):
    """
    This pattern matches the start of the comment
    """
    pattern: Pattern = re.compile('^(//|/\*)')

    _NAME_MAP = {
        '//': 'inlinecmt',
        '/*': 'blockcmt'
    }

    def __init__(self, code: str):
        lexm = Comment.pattern.match(code).group()
        super().__init__(Comment.extract_comment(code), Comment._NAME_MAP[lexm])

    def get_num_lines(self):
        return self.lexeme.count('\n')

    @staticmethod
    def extract_comment(code: str) -> str:
        # extract the start of the comment
        opening = Comment.pattern.match(code).group()
        if opening == '//':
            # single line comment, return the first line
            return code.split('\n')[0]
        else:
            return Comment.extract_multiline(code)

    @staticmethod
    def extract_multiline(code: str) -> str:
        stack = []
        for i, c in enumerate(code):
            # look for new opening for nested comments
            if c == '/' and i < len(code) - 1 and code[i + 1] == '*':
                stack.append('/*')
            elif c == '*' and i < len(code) - 1 and code[i + 1] == '/':
                if len(stack) == 1:
                    # end of comment
                    # the comment goes up to i + 1
                    return code[:i + 2]
                else:
                    # end of nested comment
                    stack = stack[1::]
        # shouldn't get here....
        # if it gets here it returns all of the codegenr, unterminated comment
        return code

    @staticmethod
    def match(code: str) -> bool:
        return Comment.pattern.match(code) is not None
