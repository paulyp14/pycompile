"""
Define the base classes
"""
from __future__ import annotations

from typing import List, Union, Tuple

from pycompile.lex.token import *
from pycompile.utils.stack import Stack


class AbstractSyntaxNode:
    NUM_NODES: Union[int, Tuple[int, int]] = -1

    def __init__(self,
                 parent: AbstractSyntaxNode = None,
                 siblings: List[AbstractSyntaxNode] = None,
                 leftmost_sibling: AbstractSyntaxNode = None,
                 right_sibling: AbstractSyntaxNode = None,
                 **kwargs,
                 ):

        self.parent: AbstractSyntaxNode = parent
        self.siblings: List[AbstractSyntaxNode] = siblings
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
