from typing import Any, Dict

from pycompile.lex.token import *

class StackEmptyException(Exception):
    def __init__(self):
        super().__init__('Stack is empty')


class Stack:

    def __init__(self):
        self.items: list = []

        self.reverse_lookup: Dict = {
            Id: 'Id',
            Integer: 'Integer',
            Float: 'Float',
            String: 'String'
        }

    def push(self, item: Any):
        self.items.append(item)

    def pop(self) -> Any:
        if len(self.items) == 0:
            raise StackEmptyException()

        popped_item = self.items[-1]
        self.items = self.items[:-1]
        return popped_item

    def __len__(self):
        return len(self.items)

    def peek(self) -> Any:
        return self.items[-1]

    def empty(self):
        self.items = []

    def is_empty(self) -> bool:
        return len(self.items) == 0

    def contents(self) -> str:
        if len(self.items) == 0:
            return ''
        return ', '.join([self.get_repr(item) for item in self.items])

    def get_repr(self, item) -> str:
        if isinstance(item, str):
            return item
        elif isinstance(item, Token):
            return item.lexeme
        else:
            return self.reverse_lookup[item]