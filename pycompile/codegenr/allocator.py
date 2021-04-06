from __future__ import annotations
from enum import Enum

from pycompile.symbol.visitor import Visitor
from pycompile.symbol.stable import SymbolTable
from pycompile.parser.syntax.ast import AbstractSyntaxNode
from pycompile.symbol.record import SemanticRecord, TypeEnum, Type


class MemoryByteSize(Enum):
    String = 1
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
        self.first_node: AbstractSyntaxNode = None

    def pre_visit(self, node: AbstractSyntaxNode):
        if self.first_node is None:
            self.first_node = node

    def visit(self, node: AbstractSyntaxNode):
        if node.sym_table is not None:
            # node.sym_table: SymbolTable
            node.sym_table.compute_size(self, self.first_pass)

    def compute_from_record(self, record: SemanticRecord, first_pass: bool) -> int:
        rec_type: TypeEnum = record.type.enum
        if rec_type in (TypeEnum.Integer, TypeEnum.Float, TypeEnum.String):
            return MemoryByteSize.get_allocated_size(rec_type).value
        elif rec_type == TypeEnum.Void:
            # not convinced this would happen
            return 0
        elif not first_pass:
            # have to look up size of thing in symbol table
            return self.global_table.records[record.type.type_name].table_link.req_mem
        else:
            # during first pass, only calculate size of known types
            return 0

    def finish(self):
        self.first_pass = False
        self.first_node.accept(self)