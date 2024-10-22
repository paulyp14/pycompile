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
        self.sem_rec = None
        self.type_rec = None
        self.sym_table = None
        self.temp_var = None

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

    def collect(self, collector, level, parent_name=None):
        # do graph viz stuff
        viz_name = self.__class__.__name__
        if viz_name not in collector.node_names.keys():
            collector.node_names[viz_name] = 0
        node_name = f'{viz_name}{collector.node_names[viz_name] + 1}'
        collector.node_names[viz_name] += 1
        if 'token' in self.__dict__.keys() and self.token is not None:
            collector.grph.node(node_name, self.token.lexeme)
        else:
            collector.grph.node(node_name)
        if parent_name is not None:
            collector.grph.edge(parent_name, node_name)
        # do manual viz stuff
        collector.add(self, level)
        for child in self.get_children():
            child.collect(collector, level + 1, node_name)

    def __eq__(self, node: AbstractSyntaxNode):
        return isinstance(node, AbstractSyntaxNode) and self.unique_id == node.unique_id

    def is_child(self, node: AbstractSyntaxNode):
        for child in self.get_children():
            if child == node:
                return True
        return False

    def get_children(self) -> List[AbstractSyntaxNode]:
        the_children = []
        for child in self.CHILDREN:
            child_prop = self.__dict__[child]
            if isinstance(child_prop, AbstractSyntaxNode):
                the_children.append(child_prop)
            elif isinstance(child_prop, list) and len(child_prop) > 0:
                for small_child in child_prop:
                    the_children.append(small_child)
        return the_children

    def accept(self, visitor):
        visitor.pre_visit(self)
        for i, child in enumerate(self.get_children()):
            if i > 0:
                visitor.mid_visit(i, self)
            child.accept(visitor)
        visitor.visit(self)


class AbstractSyntaxTree:
    def __init__(self, node: AbstractSyntaxNode = None):
        self.head: AbstractSyntaxNode = node
