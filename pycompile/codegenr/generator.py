from typing import List, Optional, Union

from pycompile.utils.stack import Stack
from pycompile.parser.syntax.node import *
from pycompile.symbol.visitor import Visitor
from pycompile.symbol.stable import SymbolTable
from pycompile.symbol.record import SemanticRecord



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
        for i in [i for i in range(1, 13)][-1::-1]:
            self.registers.push(f"r{i}")
        # streams
        self.data_stream: List[str] = []
        self.code_stream: List[str] = []

        self.accept: bool = False
        self.current_offset: int = 0
        self.result_stack: Stack = Stack()
        self.current_scope: Optional[SymbolTable] = None

    def __add_to_code_stream(self, instruction: str, label: str = None, comment_text: str = None, comment_position: str = 'above'):
        self.__add_to_stream("CODE", instruction=instruction, label=label, comment_text=comment_text, comment_position=comment_position)

    def __add_to_data_stream(self, size: int, label: str = None, comment_text: str = None, comment_position: str = 'above'):
        instruction = f'res {size}'
        if label is None:
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
            self.__add_to_code_stream('addi r10,r0,topaddr')
            self.__add_to_code_stream('subi r10,r10,4')
            self.__add_to_code_stream('subi r14,r10,0')
            self.data_stream.append(self.__format_visual_break('MEMORY ALLOCATION'))
            self.__add_to_data_stream(size=20, label='buf', comment_text='% RESERVE BUFFER FOR WRITE FUNCTION', comment_position='inline')

        if isinstance(node, FuncBody) and isinstance(node.parent, ProgramNode):
            self.accept = True
        if node.sym_table is not None:
            self.current_scope = node.sym_table

    def visit(self, node: AbstractSyntaxNode):
        if isinstance(node, ProgramNode):
            self.__add_to_code_stream('hlt', comment_text=self.__format_visual_break('END PROGRAM'), comment_position='below')

        elif self.accept and isinstance(node, VarDecl):
            # entry = self.global_table.records['main'].table_link.records[]
            # TODO no longer necessary i don't think
            # self.__reserve_variable_memory(node)
            pass

        elif self.accept:
            # mostly just moving the reserved register up the chain
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
                if use_temp:
                    node.temp_var = res_reg
                else:
                    node.sem_rec = res_reg
            elif isinstance(node, (Signed, Negation)):
                # PERFORM OPERATION
                pass
            elif isinstance(node, Var):
                pass
            elif isinstance(node, Operator):
                # PERFORM OPERATION
                self.__binary_op(node)
            elif isinstance(node, Write):
                self.__write(node)

            elif isinstance(node, Term):
                pass
        # pop
        if node.sym_table is not None:
            self.current_scope = None

    def __write(self, node: Write):

        val_reg = self.registers.pop()
        buf_reg = self.registers.pop()
        use_temp = node.expr.temp_var is not None
        self.__load_word(node.expr, val_reg, use_temp=use_temp)
        stack_instr = f'addi r14,r14,-{self.current_scope.req_mem}'
        comment = '% increment stack frame'
        self.__add_to_code_stream(stack_instr, comment_text=comment, comment_position='inline')
        self.__store_word('-8(r14)', val_reg, comment='% put value to print on stack frame')
        instr = f'addi {buf_reg},r0,buf'
        comment = '% put address of bugger on stack frame'
        self.__add_to_code_stream(instr, comment_text=comment, comment_position='inline')
        self.__store_word('-12(r14)', buf_reg, comment=comment)
        instr = 'jl r15,intstr'
        self.__add_to_code_stream(instr, comment_text='% jump to intstr subroutine', comment_position='inline')
        self.__store_word('-8(r14)', 'r13', comment='% put result on stack for putstr')
        self.__add_to_code_stream('jl r15,putstr', comment_text='% jump to putstr subroutine', comment_position='inline')
        stack_instr = f'subi r14,r14,-{self.current_scope.req_mem}'
        self.__add_to_code_stream(stack_instr, comment_text='% decrement stack frame', comment_position='inline')
        self.registers.push(buf_reg)
        self.registers.push(val_reg)

        """
        val_reg = self.registers.pop()
        use_temp = node.expr.temp_var is not None
        self.__load_word(node.expr, val_reg, use_temp=use_temp)
        self.__add_to_code_stream(f'putc {val_reg}', comment_text='% print the value', comment_position='inline')
        """

    def __store_word(self, left_op: Union[str, AbstractSyntaxNode], register: str, use_temp: bool = True, comment: str = None):
        if isinstance(left_op, AbstractSyntaxNode):
            var = left_op.temp_var if use_temp else left_op.sem_rec
            offset = self.__get_var_offset_str(var)
            comment = comment = f'% store value in {var.name}'
        else:
            offset = left_op
        instr = f'sw {offset},{register}'
        self.__add_to_code_stream(instr, comment_text=comment, comment_position='inline')

    def __load_word(self, node: AbstractSyntaxNode, register: str, use_temp: bool = True):
        var = node.temp_var if use_temp else node.sem_rec
        instr = f'lw {register},{self.__get_var_offset_str(var)}'
        comment = f'% load value for {var.name}'
        self.__add_to_code_stream(instr, comment_text=comment, comment_position='inline')

    def __binary_op(self, node: Operator):
        right_reg = self.registers.pop()
        # LOAD RIGHT
        self.__load_word(node.right_operand, right_reg, use_temp=node.right_operand.temp_var is not None)
        if node.operator != '=':
            temp_reg = self.registers.pop()
            left_reg = self.registers.pop()
            # LOAD LEFT
            self.__load_word(node.left_operand, left_reg, use_temp=node.left_operand.temp_var is not None)
            # DO THE OPERATION
            op_str = self.op_trans[node.operator]
            instr = f'{op_str} {temp_reg},{left_reg},{right_reg}'
            self.__add_to_code_stream(instruction=instr)
            store_node = node
            use_temp = store_node.temp_var is not None
        else:
            temp_reg = right_reg
            store_node = node.left_operand
            use_temp = False
        # store the result
        self.__store_word(store_node, temp_reg, use_temp=use_temp)
        if node.operator != '=':
            self.registers.push(left_reg)
            self.registers.push(temp_reg)
        self.registers.push(right_reg)

    def __load_literal(self, node: Factor):
        register = self.registers.pop()
        literal = node.child.token.lexeme
        # TODO what happens for literals of different types?
        instr = f'addi {register},r0,{literal}'
        comment = f'% load literal: {literal}'
        self.__add_to_code_stream(instr, comment_text=comment, comment_position='inline')
        self.__store_word(node, register)
        self.registers.push(register)

    @staticmethod
    def __get_var_offset_str(var: SemanticRecord) -> str:
        return f'{0 - var.mem_offset}(r14)'

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
