"""
Define the base classes
"""
from __future__ import annotations

from typing import List, Union, Tuple

from pycompile.lex.token import *
from pycompile.utils.stack import Stack


class AbstractSyntaxNode:
    NUM_NODES: Union[int, Tuple[int, int]] = -1
    CHILDREN: List[str] = []
    NODE_COUNT = 0

    def __init__(self,
                 parent: AbstractSyntaxNode = None,
                 siblings: List[AbstractSyntaxNode] = None,
                 leftmost_sibling: AbstractSyntaxNode = None,
                 right_sibling: AbstractSyntaxNode = None,
                 **kwargs,
                 ):
        self.unique_id = AbstractSyntaxNode.__generate_unique_id()
        self.parent: AbstractSyntaxNode = parent
        self.siblings: List[AbstractSyntaxNode] = siblings
        self.right_sibling: AbstractSyntaxNode = right_sibling
        self.leftmost_sibling: AbstractSyntaxNode = leftmost_sibling

        for key, item in kwargs.items():
            if isinstance(item, AbstractSyntaxNode):
                item.parent = self
            elif isinstance(item, list) and len(item) > 0 and isinstance(item[0], AbstractSyntaxNode):
                for list_item in item:
                    list_item.parent = self

    @staticmethod
    def __generate_unique_id():
        node_id = AbstractSyntaxNode.NODE_COUNT
        AbstractSyntaxNode.NODE_COUNT += 1
        return node_id

    def make_sibling(self, node):
        ...

    def adopt_children(self, nodes: List):
        ...

    def adopt_child(self, node):
        ...

    def make_family(self, *args):
        ...

    def as_array(self):
        children = '  |  '.join(self.CHILDREN)
        name = self.__class__.__name__
        lines = [name]
        if 'operator' in self.__dict__.keys():
            lines.append(f'Operation: {self.operator}')
        if 'token' in self.__dict__.keys() and self.token.lexeme is not None:
            lines.append(f'Token: {self.token.lexeme}')
        if len(children) > 0:
            lines.append(children)
        node_max = max([len(l) for l in lines])
        diff = node_max - len(name)
        if diff > 0:
            left_pad = int(diff / 2)
            right_pad = diff - left_pad
            left_pad = left_pad * ' '
            right_pad = right_pad * ' '
        else:
            left_pad, right_pad = '', ''
        lines[0] = f'{left_pad}{name}{right_pad}'

        return lines

    def node_length_as_str(self):
        children = '  |  '.join(self.CHILDREN)
        name = self.__class__.__name__
        lines = [name]
        if 'operator' in self.__dict__.keys():
            lines.append(f'Operation: {self.operator}')
        if 'token' in self.__dict__.keys() and self.token.lexeme is not None:
            lines.append(f'Token: {self.token.lexeme}')
        lines.append(children)
        ln = max([len(l) for l in lines])
        return ln + 4

    def __str__(self):
        return '\n'.join(self.as_array())

    def collect(self, collector, level):
        collector.add(self, level)
        for child in self.CHILDREN:
            child_prop = self.__dict__[child]
            if isinstance(child_prop, AbstractSyntaxNode):
                child_prop.collect(collector, level + 1)
            elif isinstance(child_prop, list) and len(child_prop) > 0:
                for small_child in child_prop:
                    small_child.collect(collector, level + 1)

    def __eq__(self, node: AbstractSyntaxNode):
        return isinstance(node, AbstractSyntaxNode) and self.unique_id == node.unique_id

    def is_child(self, node: AbstractSyntaxNode):
        for child in self.CHILDREN:
            child_prop = self.__dict__[child]
            if isinstance(child_prop, AbstractSyntaxNode):
                if child_prop.__eq__(node):
                    return True
            elif isinstance(child_prop, list) and len(child_prop) > 0:
                for small_child in child_prop:
                    if isinstance(small_child, AbstractSyntaxNode) and small_child.__eq__(node):
                        return True
        return False


class AbstractSyntaxTree:
    def __init__(self, node: AbstractSyntaxNode = None):
        self.head: AbstractSyntaxNode = node
