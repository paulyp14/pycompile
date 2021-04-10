from typing import List

from pycompile.utils.stack import Stack
from pycompile.symbol.visitor import Visitor, Signed
from pycompile.symbol.stable import SymbolTable
from pycompile.parser.syntax.node import (
    AbstractSyntaxNode, ProgramNode, VarDecl, FuncBody, Var, Operator, Factor, Term, Leaf,
    Negation, ArithExpr, Expr
)


class CodeGenerator(Visitor):

    op_trans = {
        '*': 'mul',
        '+': 'add',
        '-': 'sub',
        '/': 'div',
        '=': 'sw'
    }

    def __init__(self, symbol_table: SymbolTable = None):
        super().__init__(symbol_table=symbol_table)
        # set up registers
        self.registers: Stack = Stack()
        for i in range(1, 14):
            self.registers.push(f"r{i}")
        # streams
        self.data_stream: List[str] = []
        self.code_stream: List[str] = []

        self.accept: bool = False
        self.current_offset: int = 0
        self.result_stack: Stack = Stack()

    def __add_to_code_stream(self, instruction: str, label: str = None, comment_text: str = None, comment_position: str = 'above'):
        self.__add_to_stream("CODE", instruction=instruction, label=label, comment_text=comment_text, comment_position=comment_position)

    def __add_to_data_stream(self, size: int, comment_text: str = None, comment_position: str = 'above'):
        instruction = f'res {size}'
        label = f'{0 - self.current_offset}'
        self.current_offset += size
        self.__add_to_stream("DATA", instruction=instruction, label=label, comment_text=comment_text, comment_position=comment_position)

    def __add_to_stream(self, stream: str, instruction: str, label: str = None, comment_text: str = None, comment_position: str = 'above'):
        max_indent = 15
        max_istr = 30
        stream = self.code_stream if stream == 'CODE' else self.data_stream
        # add comment line
        inline_comment = None
        if comment_text is not None and comment_position == 'inline':
            inline_comment = comment_text
        elif comment_text is not None and comment_position == 'above':
            stream.append(f'{comment_text}')
        if label is None:
            label = ""
        padding = max_indent - len(label)
        inline_comment_str = ""
        if inline_comment is not None:
            inline_comment_str = f'{(max_istr - len(instruction)) * " "}{inline_comment}'
        stream.append(f'{label}{padding * " "}{instruction}{inline_comment_str}')
        if comment_text is not None and comment_position == 'below':
            stream.append(comment_text)

    def pre_visit(self, node: AbstractSyntaxNode):
        if isinstance(node, ProgramNode):
            self.__add_to_code_stream('entry', comment_text=self.__format_visual_break('BEGIN PROGRAM'))
            self.__add_to_code_stream('addi r14,r0,topaddr')
            self.data_stream.append(self.__format_visual_break('MEMORY ALLOCATION'))
            self.__add_to_data_stream(size=20, comment_text='% RESERVE BUFFER FOR WRITE FUNCTION', comment_position='inline')

        if isinstance(node, FuncBody) and isinstance(node.parent, ProgramNode):
            self.accept = True

    def visit(self, node: AbstractSyntaxNode):
        if isinstance(node, ProgramNode):
            self.__add_to_code_stream('hlt', comment_text=self.__format_visual_break('END PROGRAM'), comment_position='below')

        elif self.accept and isinstance(node, VarDecl):
            # entry = self.global_table.records['main'].table_link.records[]
            # TODO no longer necessary i don't think
            self.__reserve_variable_memory(node)

        elif self.accept:
            # mostly just moving the reserved register up the chain
            if isinstance(node, Factor):
                # can be Leaf or Var or Signed or Not
                # if its a leaf, get a register and put the value
                if isinstance(node.child, Leaf):
                    self.__load_literal(node)
                else:
                    node.reserved_register = node.child.reserved_register
                pass
            elif isinstance(node, (ArithExpr, Expr, Term)):
                # migrate the register
                if isinstance(node, (ArithExpr, Expr)):
                    res_reg = node.arith_expr.reserved_register
                else:
                    res_reg = node.factor.reserved_register
                node.reserved_register = res_reg
            elif isinstance(node, (Signed, Negation)):
                # PERFORM OPERATION
                pass
            elif isinstance(node, Var):
                pass
            elif isinstance(node, Operator):
                # PERFORM OPERATION
                self.__binary_op(node)

            elif isinstance(node, Term):
                pass

    def __binary_op(self, node: Operator):

        left_reg = node.left_operand.reserved_register
        right_reg = node.right_operand.reserved_register
        temp_reg = self.registers.pop()
        op_str = self.op_trans[node.operator]
        instr = f'{op_str} {temp_reg},{left_reg},{right_reg}'
        self.__add_to_code_stream(instruction=instr)
        self.registers.push(left_reg)
        self.registers.push(right_reg)
        node.reserved_register = temp_reg

    def __load_literal(self, node: Factor):
        register = self.registers.pop()
        literal = node.child.token.lexeme
        # TODO what happens for literals of different types?
        instr = f'addi {register},r0,{literal}'
        node.reserved_register = register
        self.__add_to_code_stream(instr)

    @staticmethod
    def __format_visual_break(comment_text) -> str:
        req_len = 100
        beg = f'%  ====== {comment_text} '
        return f'{beg}{"=" * (req_len - len(beg))}'

    def __reserve_variable_memory(self, node: AbstractSyntaxNode):
        res_comment = f'% Reserve space for variable {node.sem_rec.name}'
        self.__add_to_data_stream(node.sem_rec.memory_size, comment_text=res_comment, comment_position='inline')

    def finish(self):
        print()
