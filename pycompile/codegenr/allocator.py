from __future__ import annotations
import operator
from enum import Enum
from functools import reduce
from typing import List, Dict, Union, Optional

from pycompile.parser.syntax.node import *
from pycompile.symbol.visitor import Visitor
from pycompile.symbol.stable import SymbolTable
from pycompile.codegenr.frame import StackFrame
from pycompile.parser.syntax.ast import AbstractSyntaxNode
from pycompile.symbol.record import SemanticRecord, TypeEnum, Type, Kind


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
        self.current_scope: Optional[SymbolTable] = None

    def pre_visit(self, node: AbstractSyntaxNode):
        if self.first_node is None:
            self.first_node = node
        if node.sym_table is not None:
            self.current_scope = node.sym_table

    def visit(self, node: AbstractSyntaxNode):
        if not self.final_pass and node.sym_table is not None:
            if isinstance(node.parent, ProgramNode) or isinstance(node, ProgramNode):
                is_function = False
            else:
                is_function = node.sem_rec.kind == Kind.Function
            node.sym_table.compute_size(self, self.first_pass, is_function)

        if not self.final_pass and not self.first_pass:
            if isinstance(node, Factor):
                # can be Leaf or Var or Signed or Not
                # if its a leaf, get a register and put the value
                if isinstance(node.child, Leaf):
                    self.__load_literal(node)
                else:
                    use_temp = node.child.temp_var is not None
                    if use_temp:
                        node.temp_var = node.child.temp_var
                    else:
                        node.sem_rec = node.child.sem_rec
            elif isinstance(node, (ArithExpr, Expr, Term)):
                # migrate the register
                if isinstance(node, (ArithExpr, Expr)):
                    use_temp = node.arith_expr.temp_var is not None
                    res_reg = node.arith_expr.temp_var if use_temp else node.arith_expr.sem_rec
                else:
                    use_temp = node.factor.temp_var is not None
                    res_reg = node.factor.temp_var if use_temp else node.factor.sem_rec
                node.temp_var = res_reg
            elif isinstance(node, Signed):
                # PERFORM OPERATION
                self.__signed(node)
            elif isinstance(node, Negation):
                self.__negation(node)
            elif isinstance(node, Var):
                pass
            elif isinstance(node, Operator):
                # PERFORM OPERATION
                self.__binary_op(node)
            # pop
        if node.sym_table is not None:
            self.current_scope = None

    def __next_temp_name(self):
        return f'temp_{self.current_scope.var}'

    def __signed(self, node: Signed):
        if node.op == '+':
            return
        temp_name = f'$temp_{self.current_scope.next_temp_var_id()}'
        temp_rec = SemanticRecord(temp_name, Kind.Variable, record_type=node.factor.type_rec.type)
        self.current_scope.add_record(temp_rec)
        node.temp_var = temp_rec

    def __negation(self, node: Negation):
        temp_name = temp_name = f'$temp_{self.current_scope.next_temp_var_id()}'
        temp_rec = SemanticRecord(temp_name, Kind.Variable, record_type=node.type_rec.type)
        self.current_scope.add_record(temp_rec)
        node.temp_var = temp_rec

    def __load_literal(self, node: Factor):
        temp_name = f'$temp_{self.current_scope.next_temp_var_id()}'
        # the type should come from the type of the expr???
        temp_rec = SemanticRecord(temp_name, Kind.Variable, record_type=Type.get_type_from_token(node))
        self.current_scope.add_record(temp_rec)
        node.temp_var = temp_rec

    def __binary_op(self, node: Operator):
        if node.operator == '=':
            # ASSIGN DOES NOT REQUIRE TEMP
            return
        temp_name = f'$temp_{self.current_scope.next_temp_var_id()}'
        # use LEFT if operator is not ASSIGN
        # assign has to go into something that is not $TEMP
        using = node.left_operand if node.operator != '=' else node.right_operand
        use_temp = using.temp_var is not None
        temp: SemanticRecord = using.temp_var if use_temp else using.sem_rec
        # the type should come from the type of the expr???
        temp_rec = SemanticRecord(temp_name, Kind.Variable, record_type=temp.type)
        self.current_scope.add_record(temp_rec)
        if use_temp:
            node.temp_var = temp_rec
        else:
            node.sem_rec = temp_rec

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
