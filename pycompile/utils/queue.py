from typing import List, Any


class Queue:

    def __init__(self):
        self.items: List[Any] = []

    def add(self, *args):
        self.items.extend(args)

    def remove(self) -> Any:
        to_return = self.items[0]
        self.items = self.items[1:]
        return to_return

    def peek_last(self) -> Any:
        return self.items[-1]

    def peek_first(self) -> Any:
        return self.items[0]

    def is_empty(self) -> bool:
        return len(self.items) == 0

    def __len__(self) -> int:
        return len(self.items)