"""
Define the base classes
"""
from typing import List, Union, Tuple


class AbstractSyntaxNode:
    NUM_NODES: Union[int, Tuple[int, int]] = -1

    def __init__(self,
                 parent=None,
                 siblings: List = None,
                 children: List = None,
                 leftmost_sibling=None,
                 right_sibling=None):

        self.parent: AbstractSyntaxNode = parent
        self.siblings: List[AbstractSyntaxNode] = siblings
        self.children: List[AbstractSyntaxNode] = children
        self.right_sibling: AbstractSyntaxNode = right_sibling
        self.leftmost_sibling: AbstractSyntaxNode = leftmost_sibling

    def make_sibling(self, node):
        ...

    def adopt_children(self, nodes: List):
        ...

    def adopt_child(self, node):
        ...

    def make_family(self, *args):
        ...


class AbstractSyntaxTree:
    def __init__(self, node: AbstractSyntaxNode = None):
        self.head: AbstractSyntaxNode = node
