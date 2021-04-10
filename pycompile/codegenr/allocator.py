from __future__ import annotations
import operator
from enum import Enum
from functools import reduce
from typing import List, Dict, Union

from pycompile.symbol.visitor import Visitor
from pycompile.symbol.stable import SymbolTable
from pycompile.codegenr.frame import StackFrame
from pycompile.parser.syntax.ast import AbstractSyntaxNode
from pycompile.symbol.record import SemanticRecord, TypeEnum, Type
from pycompile.parser.syntax.node import FuncBody, ProgramNode


class MemoryByteSize(Enum):
    String = 4
    Integer = 4
    Float = 8

    @staticmethod
    def get_allocated_size(rec_type: TypeEnum) -> MemoryByteSize:
        trans = {
            TypeEnum.Float: MemoryByteSize.Float,
            TypeEnum.Integer: MemoryByteSize.Integer,
            TypeEnum.String: MemoryByteSize.String
        }
        return trans[rec_type]


class MemoryAllocator(Visitor):

    def __init__(self, symbol_table: SymbolTable = None):
        super().__init__(symbol_table=symbol_table)
        self.first_pass: bool = True
        self.final_pass: bool = False
        self.stack_frames: List[StackFrame] = []
        self.first_node: AbstractSyntaxNode = None

    def pre_visit(self, node: AbstractSyntaxNode):
        if self.first_node is None:
            self.first_node = node

    def visit(self, node: AbstractSyntaxNode):
        if not self.final_pass and node.sym_table is not None:
            node.sym_table.compute_size(self, self.first_pass)
        # TODO determine if this is needed after all....
        elif self.final_pass:
            if isinstance(node, FuncBody) and isinstance(node.parent, ProgramNode):
                self.stack_frames.append(StackFrame(node.sym_table))

    def compute_from_record(self, record: SemanticRecord, first_pass: bool) -> int:
        rec_type: TypeEnum = record.type.enum
        if rec_type in (TypeEnum.Integer, TypeEnum.Float, TypeEnum.String):
            if not record.is_array:
                return MemoryByteSize.get_allocated_size(rec_type).value
            else:
                return self.__allocate_array(record)
        elif rec_type == TypeEnum.Void:
            # not convinced this would happen
            return 0
        elif not first_pass:
            # have to look up size of thing in symbol table
            if not record.is_array:
                return self.global_table.records[record.type.type_name].table_link.req_mem
            else:
                return self.__allocate_array(record)
        else:
            # during first pass, only calculate size of known types
            return 0

    def __validate_array(self, record: SemanticRecord) -> bool:
        # determines if array can be statically allocated
        if record.dimension_dict is None:
            return False
        if record.dimension_dict is not None and len(record.dimension_dict.keys()) < record.dimensions:
            return False
        if record.dimensions != sum([1 for k, v in record.dimension_dict.items() if isinstance(v, int)]):
            return False
        return True

    def __allocate_array(self, record: SemanticRecord) -> int:
        if self.__validate_array(record):
            rec_type = record.type.enum
            entries = reduce(operator.mul, record.dimension_dict.values())
            if rec_type in (TypeEnum.Integer, TypeEnum.Float, TypeEnum.String):
                return MemoryByteSize.get_allocated_size(rec_type).value * entries
            else:
                return self.global_table.records[record.type.type_name].table_link.req_mem * entries
        else:
            return 4

    def finish(self):
        self.first_pass = False
        self.first_node.accept(self)
        # TODO determine if necessary
        # TODO what happens if class is declared that has reference to class defined after it?
        #       in second pass might compute the size of the class erroneously...
        #       maybe implement a while loop that computes in each iteration the classes it can until none are left...
        self.final_pass = True
        self.first_node.accept(self)
