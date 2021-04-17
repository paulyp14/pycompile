from typing import List, Optional, Union

from pycompile.utils.queue import Queue
from pycompile.utils.stack import Stack
from pycompile.parser.syntax.node import *
from pycompile.symbol.visitor import Visitor
from pycompile.symbol.stable import SymbolTable
from pycompile.symbol.record import SemanticRecord, Kind, TypeEnum, TypeRecord


class CodeGenerator(Visitor):

    op_trans = {
        '*': 'mul',
        '+': 'add',
        '-': 'sub',
        '/': 'div',
        '=': 'sw',
        '>': 'cgt',
        '>=': 'cge',
        '<': 'clt',
        '<=': 'cle',
        '&': 'and',
        '|': 'or',
        '==': 'ceq',
        '<>': 'cne'
    }

    req_comment_len = 150
    max_indent = 15
    max_istr = 30

    def __init__(self, symbol_table: SymbolTable = None):
        super().__init__(symbol_table=symbol_table)
        # set up registers
        self.registers: Stack = Stack()
        for i in [i for i in range(1, 13)][-1::-1]:
            self.registers.push(f"r{i}")
        # streams
        self.data_stream: List[str] = []
        self.func_stream: List[str] = []
        self.main_stream: List[str] = []
        self.code_stream: List[str] = self.func_stream

        self.accept: bool = False
        self.in_main: bool = False
        self.from_var: Optional[bool] = None
        self.current_offset: int = 0
        self.result_stack: Stack = Stack()
        self.current_scope: Optional[SymbolTable] = None
        self.current_label_idxs: dict = {
            'if': 0,
            'while': 0
        }
        self.next_label: Optional[str] = None
        self.stream_stack_key: Stack() = Stack()
        self.control_flow_node_stack: Stack = Stack()
        self.control_flow_stream_stack: Stack = Stack()

    def __generate_control_flow_label(self) -> str:
        key = 'if' if isinstance(self.control_flow_node_stack.peek(), If) else 'while'
        idx = self.current_label_idxs[key]
        self.current_label_idxs[key] += 1
        return f'{key}_{idx}'

    def __get_func_label(self, func_name: str) -> str:
        as_label = f'F_{func_name}'
        if as_label not in self.current_label_idxs.keys():
            self.current_label_idxs[as_label] = 0
        final_label = f'{as_label}_{self.current_label_idxs[as_label]}'
        self.current_label_idxs[as_label] += 1
        return final_label

    def __add_to_code_stream(self, instruction: str, label: str = None, comment_text: str = None, comment_position: str = 'above', add_label: bool = True):
        stream_obj = None
        if not self.control_flow_stream_stack.is_empty():
            stream_obj = self.control_flow_stream_stack.peek()[self.stream_stack_key.peek()]
            if len(stream_obj) == 0:
                label = self.control_flow_stream_stack.peek()['label']
                if self.stream_stack_key.peek() not in ('if', 'while'):
                    label = f'{label}_{self.stream_stack_key.peek()}'
        if self.next_label is not None:
            if label is not None:
                self.__add_to_stream("CODE", instruction=f'j {label}', label=self.next_label,
                                     comment_text='% add intermediate jump to prevent conflicting labels',
                                     comment_position='inline', stream_obj=stream_obj, add_label=add_label)
            else:
                label = self.next_label
            self.next_label = None
        self.__add_to_stream("CODE", instruction=instruction, label=label, comment_text=comment_text, comment_position=comment_position, stream_obj=stream_obj, add_label=add_label)

    def __add_to_data_stream(self, size: int, label: str = None, comment_text: str = None, comment_position: str = 'above'):
        instruction = f'res {size}'
        if label is None:
            label = f'{0 - self.current_offset}'
        self.current_offset += size
        self.__add_to_stream("DATA", instruction=instruction, label=label, comment_text=comment_text, comment_position=comment_position)

    def __add_to_stream(self,
                        stream: str,
                        instruction: str,
                        label: str = None,
                        comment_text: str = None,
                        comment_position: str = 'above',
                        stream_obj: List = None,
                        add_label: bool = True):

        if stream_obj is None:
            stream = self.code_stream if stream == 'CODE' else self.data_stream
        else:
            stream = stream_obj
        # add comment line
        inline_comment = None
        if comment_text is not None and comment_position == 'inline':
            inline_comment = comment_text
        elif comment_text is not None and comment_position == 'above':
            stream.append(f'{comment_text}')
        if label is None:
            label = ""
        if add_label:
            padding = self.max_indent - len(label)
        else:
            padding = 0
        inline_comment_str = ""
        if inline_comment is not None:
            inline_comment_str = f'{(self.max_istr - len(instruction)) * " "}{inline_comment}'
        stream.append(f'{label}{padding * " "}{instruction}{inline_comment_str}')
        if comment_text is not None and comment_position == 'below':
            stream.append(comment_text)

    def pre_visit(self, node: AbstractSyntaxNode):
        if isinstance(node, ProgramNode):
            max_len = max([len(rec.name) for rec in self.global_table.records.values() if rec.kind == Kind.Function])
            self.max_indent = max(max_len + 8, self.max_indent)

        elif isinstance(node, FuncBody):
            self.accept = True

        if isinstance(node, FuncBody) and isinstance(node.parent, ProgramNode):
            self.in_main = True
            self.code_stream = self.main_stream
            self.__add_to_code_stream('entry', comment_text=self.__format_visual_break('BEGIN PROGRAM'))
            self.__add_to_code_stream('addi r10,r0,topaddr')
            self.__add_to_code_stream('subi r10,r10,4')
            self.__add_to_code_stream('subi r14,r10,0')
            self.data_stream.append(self.__format_visual_break('MEMORY ALLOCATION'))
            self.__add_to_data_stream(size=20, label='buf', comment_text='% RESERVE BUFFER FOR WRITE FUNCTION', comment_position='inline')
        elif isinstance(node, FuncBody):
            # set up function....
            func_name = node.parent.sem_rec.get_func_decl()
            needed_label = self.__get_func_label(node.parent.sem_rec.name)
            self.next_label = needed_label
            node.parent.sem_rec.func_label = needed_label
            offset = 0 - node.parent.sem_rec.return_size
            self.__add_to_code_stream(f'sw {offset}(r14),r15', comment_text=self.__format_visual_break(f'START - definition for: {func_name}'))

        elif isinstance(node, (If, While)):
            self.control_flow_node_stack.push(node)
            if isinstance(node, If):
                key = 'if'
                cf_dict = {'if': [], 'then': [], 'else': [], 'label': self.__generate_control_flow_label()}
            else:
                key = 'while'
                cf_dict = {'while': [], 'then': [], 'label': self.__generate_control_flow_label()}
            self.control_flow_stream_stack.push(cf_dict)
            self.stream_stack_key.push(key)
        if node.sym_table is not None:
            self.current_scope = node.sym_table

    def mid_visit(self, child_idx: int, node: AbstractSyntaxNode):
        not_empty = not self.control_flow_node_stack.is_empty()
        if not_empty and isinstance(node, If) and isinstance(self.control_flow_node_stack.peek(), If):
            if self.next_label is not None and 'while' in self.next_label:
                # force evaluation
                self.__add_to_code_stream('addi r0,r0,0', comment_text='% forcing insertion of next label', comment_position='inline')
            self.stream_stack_key.pop()
            self.stream_stack_key.push('then' if child_idx == 1 else 'else')
        elif not_empty and isinstance(node, While) and isinstance(self.control_flow_node_stack.peek(), While):
            # if not self.next_label is not None:
            #     # force evaluation
            #     self.__add_to_code_stream('addi r0,r0,0', comment_text='% forcing insertion of next label', comment_position='inline')
            self.stream_stack_key.pop()
            self.stream_stack_key.push('then' if child_idx == 1 else 'UHOH')

    def visit(self, node: AbstractSyntaxNode):
        if isinstance(node, ProgramNode):
            self.__add_to_code_stream('hlt', comment_text=self.__format_visual_break('END PROGRAM'), comment_position='below')
            # merge func stream into code stream
            self.code_stream.extend(self.func_stream)

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
                        node.temp_var.from_var = isinstance(node.child, Var) and self.from_var
                        self.from_var = None
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
            elif isinstance(node, Signed):
                # PERFORM OPERATION
                self.__signed(node)
            elif isinstance(node, Negation):
                self.__negation(node)
            elif isinstance(node, Var):
                self.__process_var(node)
            elif isinstance(node, Operator):
                # PERFORM OPERATION
                self.__binary_op(node)
            elif isinstance(node, Write):
                self.__write(node)
            elif isinstance(node, Read):
                self.__read(node)
            elif isinstance(node, If):
                self.__if(node)
            elif isinstance(node, While):
                self.__while(node)
            elif isinstance(node, Return):
                self.__return(node)
        # pop
        if node.sym_table is not None:
            self.current_scope = None
        if isinstance(node, FuncBody):
            self.accept = False

        if isinstance(node, FuncBody) and isinstance(node.parent, ProgramNode):
            pass
        elif isinstance(node, FuncBody):
            self.__end_func(node)

    def __return(self, node: Return):
        temp_reg = self.registers.pop()
        self.__load_word(node.expr, temp_reg)
        self.__store_word('0(r14)', temp_reg, comment='% put return value on stack')
        self.registers.push(temp_reg)

    def __end_func(self, node: FuncBody):
        func_name = node.parent.sem_rec.get_func_decl()
        offset = 0 - node.parent.sem_rec.return_size
        self.__add_to_code_stream(f'lw r15,{offset}(r14)',comment_text='% retrieve r15', comment_position='inline')
        self.__add_to_code_stream('jr r15', comment_text=self.__format_visual_break(f'END - definition for: {func_name}'), comment_position='below')

    def __process_var(self, node: Var):
        comps = node.get_children()
        temp_reg = self.registers.pop()
        acc_reg = self.registers.pop()
        self.__add_to_code_stream(f'addi {acc_reg},r0,0', comment_text='% COMPLEX VAR ACCESS: start with zero', comment_position='inline')
        # loop through each part of the complex statement
        # for each individual one, calculate the offset
        # keep running total of offsets
        for idx, base in enumerate(comps[::2]):
            list_idx = (idx * 2) + 1
            is_var = isinstance(comps[list_idx], IndList)
            self.from_var = is_var
            if is_var and idx == 0:
                self.__process_var_access(base, comps[list_idx], temp_reg)
            elif is_var:
                self.__process_var_access(base, comps[list_idx], temp_reg, prev=comps[list_idx - 3], p_list=comps[list_idx - 2])
            else:
                self.__store_word(node, temp_reg)
                self.__process_func_call(base, comps[list_idx], acc_reg)
                self.__load_word(node, temp_reg)
            if is_var:
                # subtract
                self.__add_to_code_stream(f'sub {acc_reg},{acc_reg},{temp_reg}', comment_text='% load position of index', comment_position='inline')
            else:
                # TODO this won't work if the function call is not at the end of the expression....
                pass
        self.__store_word(node, acc_reg)
        self.registers.push(temp_reg)
        self.registers.push(acc_reg)

    def __process_var_access(self, base: AbstractSyntaxNode, b_list: AbstractSyntaxNode, outer_reg: str, prev: AbstractSyntaxNode = None, p_list: AbstractSyntaxNode = None):
        temp_reg = self.registers.pop()
        acc_reg = self.registers.pop()
        type_size = self.__get_size(base.sem_rec.type)

        if len(b_list.get_children()) > 0:
            # have to calculate array offset
            self.__add_to_code_stream(f'addi {acc_reg},r0,{type_size}',
                                      comment_text='% start accumulation of array indexes', comment_position='inline')
            for idx in b_list.get_children():
                use_temp = idx.temp_var is not None
                self.__load_word(idx, temp_reg, use_temp=use_temp)
                self.__add_to_code_stream(f'mul {acc_reg},{acc_reg},{temp_reg}', comment_text='% accumulate array indexes', comment_position='inline')
        else:
            # not an array
            self.__add_to_code_stream(f'addi {acc_reg},r0,0', comment_text='% no array indexes to calculate',
                                      comment_position='inline')
        if prev is None:
            # calculate offset from the top of the frame pointer
            # need to use the address if it's a complex type
            if base.sem_rec.kind == Kind.Parameter and (base.sem_rec.is_array or base.sem_rec.type.enum == TypeEnum.Class):
                # load the address in this function of the address in the calling scope
                offset = 0 - base.sem_rec.mem_offset
                instr = f'lw {temp_reg},{offset}(r14)'
                comment = '% load the address of the variable in the outer scope'
            elif base.sem_rec.kind == Kind.Variable and base.sem_rec.member_of is not None:
                # load the address in this function of the address in the calling scope
                offset = 0 - self.current_scope.instance_ref_addr
                instr = f'lw {temp_reg},{offset}(r14)'
                comment = '% load the address of the instance whose function this is'
                self.__add_to_code_stream(instr, comment_text=comment, comment_position='inline')
                instr = f'subi {temp_reg},{temp_reg},{base.sem_rec.mem_offset}'
                comment = '% calculate the offset of the member variable from the address of the instance'
            else:
                # simply load the address of the primitive type
                instr = f'subi {temp_reg},r14,{base.sem_rec.mem_offset}'
                comment = '% calculate beginning address of variable from stack frame point'
            self.__add_to_code_stream(instr, comment_text=comment, comment_position='inline')
        else:
            # calculate the offset from the scope....
            self.__add_to_code_stream(f'subi {temp_reg},r0,{base.sem_rec.mem_offset}', comment_text='% calculate member access from offset of record in class', comment_position='inline')
        self.__add_to_code_stream(f'sub {temp_reg},{temp_reg},{acc_reg}', comment_text='% calculate array index in memory', comment_position='inline')
        self.__add_to_code_stream(f'sub {outer_reg},r0,{temp_reg}')
        self.registers.push(temp_reg)
        self.registers.push(acc_reg)

    def __get_size(self, type_):
        trans = {'string': 4, 'integer': 4, 'float': 8}
        if type_.type_name not in trans.keys():
            return self.global_table.records[type_.type_name].table_link.req_mem
        else:
            return trans[type_.type_name]

    def __process_func_call(self, base: AbstractSyntaxNode, b_list: AbstractSyntaxNode, acc_reg: str = None):
        params = [param for param in base.sem_rec.table_link.records.values() if param.kind == Kind.Parameter]
        for np, sp in zip(b_list.get_children(), params):
            reg = self.registers.pop()
            if (
                # reference type
                sp.type.enum == TypeEnum.Class or
                (
                    # both arrays
                    (sp.is_array and np.type_rec.is_array) and
                    # same number of dimensions
                    (sp.dimensions == np.type_rec.dimensions) and
                    # any declared dimensions in the semantic_record match with the
                    (sp.dimension_dict is None or self.__validate_array(sp, np.type_rec))
                )
            ):
                # we are dealing with an array, and we must copy the outer scope address of the array...
                outer_scope_offset = 0 - np.temp_var.mem_offset
                self.__add_to_code_stream(f'lw {reg},{outer_scope_offset}(r14)', comment_position='inline', comment_text='% load outer scope offset of reference-type param')
                comment = '% passing address of reference type'
                pass
            else:
                # simply COPY the simple values over
                if sp.is_array or np.type_rec.is_array:
                    print('UHOH, SOMETHING EXTREMELY WRONG')
                self.__load_word(np, reg)
                comment = '% passing function param'
            # put the value in the offset for the function that is being jumped into
            # the value will be the value of the param if it is a simple type,
            # else, it will be the address of the param in the outer scope
            offset = 0 - (self.current_scope.req_mem + sp.mem_offset)
            self.__add_to_code_stream(f'sw {offset}(r14),{reg}', comment_text=comment, comment_position='inline')
            self.registers.push(reg)
        # process member functions
        if base.sem_rec.member_of is not None:
            # need to put reference to the instance two spots below r14
            # r14 --- top of function, return address
            #     --- return type of function, if needed
            #     --- instance reference, if needed
            # this if the offset of the address to store reference to the object whose's function is being called
            containing_class_offset = 0 - (self.current_scope.req_mem + base.sem_rec.table_link.instance_ref_addr)
            # the address of the containing class is already in teh outer_reg
            left_op = f'{containing_class_offset}(r14)'
            instr = f'sw {left_op},{acc_reg}'
            comment = '% pass the reference to the instance the member function is being called on'
            self.__add_to_code_stream(instr, comment_text=comment, comment_position='inline')
        if base.sem_rec.get_name() in self.global_table.records.keys():
            master_rec = self.global_table.records[base.sem_rec.get_name()]
        else:
            master_rec = self.global_table.records[base.sem_rec.get_func_decl()]
        # save register before jumping
        self.__store_word(b_list, acc_reg)
        # stack ops and jump
        self.__add_to_code_stream(f'subi r14,r14,{self.current_scope.req_mem}', comment_text='% decrement stack frame to function', comment_position='inline')
        self.__add_to_code_stream(f'jl r15,{master_rec.func_label}')
        self.__add_to_code_stream(f'addi r14,r14,{self.current_scope.req_mem}', comment_text='% increase stack frame back to this function', comment_position='inline')
        # reload register
        # TODO ADD THIS AS ELSE....
        self.__load_word(b_list, acc_reg)
        # store the return value in the accumulated register
        if base.sem_rec.type is not None and base.sem_rec.type.enum != TypeEnum.Void:
            offset = 0 - self.current_scope.req_mem
            self.__add_to_code_stream(f'lw {acc_reg},{offset}(r14)', comment_text='% get the return value', comment_position='inline')

    def __validate_array(self, sem_rec: SemanticRecord, node_type: TypeRecord) -> bool:
        validated = True
        for key, value in sem_rec.dimension_dict.items():
            validated = value == node_type.dimensions_dict.get(key)
            if not validated:
                break
        return validated

    def __signed(self, node: Signed):
        if node.op == '+':
            # who cares
            if node.factor.temp_var is not None:
                node.temp_var = node.factor.temp_var
            else:
                node.sem_rec = node.factor.sem_rec
            return
        # requires operation
        val_reg = self.registers.pop()
        res_reg = self.registers.pop()
        sign_reg = self.registers.pop()
        use_temp = node.factor.temp_var is not None
        self.__add_to_code_stream(f'addi {sign_reg},r0,-1', comment_text='% load -1 to flip the sign', comment_position='inline')
        self.__load_word(node.factor, val_reg, use_temp=use_temp)
        self.__add_to_code_stream(f'mul {res_reg},{val_reg},{sign_reg}', comment_text='% perform operation', comment_position='inline')
        self.__store_word(node, res_reg)
        self.registers.push(val_reg)
        self.registers.push(res_reg)
        self.registers.push(sign_reg)

    def __negation(self, node: Negation):
        val_reg = self.registers.pop()
        temp_reg = self.registers.pop()
        use_temp = node.factor.temp_var is not None
        self.__load_word(node.factor, val_reg, use_temp=use_temp)
        self.__add_to_code_stream(f'not {temp_reg},{val_reg}', comment_text='% perform negation', comment_position='inline')
        self.__store_word(node, temp_reg)
        self.registers.push(val_reg)
        self.registers.push(temp_reg)

    def __if(self, node: If):
        self.stream_stack_key.pop()
        next_label = None
        if self.next_label is not None:
            next_label = self.next_label
            self.next_label = None
        cf_label = self.control_flow_stream_stack.peek()["label"]
        end_label = f'{cf_label}_end'
        else_label = f'{cf_label}_else'
        bz_label = else_label if node.else_block is not None else end_label
        reg = self.registers.pop()
        self.stream_stack_key.push('if')
        use_temp = node.rel_expr.temp_var is not None
        self.__load_word(node.rel_expr, reg, use_temp=use_temp)
        instr = f'bz {reg},{bz_label}'
        self.__add_to_code_stream(instr, comment_text=f'% branch to {bz_label}', comment_position='inline')
        self.stream_stack_key.pop()
        self.stream_stack_key.push('then')
        self.__add_to_code_stream(f'j {end_label}', comment_text=f'% go to end {end_label}', comment_position='inline')
        self.stream_stack_key.pop()
        self.stream_stack_key.push('else')
        self.__add_to_code_stream(CodeGenerator.__format_visual_break(f"end of {cf_label}"))
        if next_label is not None:
            self.__add_to_code_stream(instruction=f'j {end_label}', label=next_label, comment_text='% add intermediate jump to prevent conflicting labels', comment_position='inline')
        self.stream_stack_key.pop()
        self.control_flow_node_stack.pop()
        cf_dict = self.control_flow_stream_stack.pop()
        for i, line in enumerate([f'begin {cf_label}'] + cf_dict['if'] + cf_dict['then'] + cf_dict['else']):
            if i == 0:
                # add visual break
                line = CodeGenerator.__format_visual_break(line, use_indent=True)
            self.__add_to_code_stream(line, add_label=False)
        self.registers.push(reg)
        self.next_label = end_label

    def __while(self, node: While):
        reg = self.registers.pop()
        next_label = None
        if self.next_label is not None:
            next_label = self.next_label
            self.next_label = None
        cf_label = self.control_flow_stream_stack.peek()["label"]
        end_label = f'{cf_label}_end'
        self.stream_stack_key.push('while')
        use_temp = node.rel_expr.temp_var is not None
        self.__load_word(node.rel_expr, reg, use_temp=use_temp)
        instr = f'bz {reg},{end_label}'
        self.__add_to_code_stream(instr, comment_text=f'% branch to {end_label}', comment_position='inline')
        self.stream_stack_key.pop()
        self.stream_stack_key.push('then')
        self.__add_to_code_stream(f'j {cf_label}', comment_text=f'% go back to start of {cf_label}', comment_position='inline')
        self.__add_to_code_stream(CodeGenerator.__format_visual_break(f"end of {cf_label}"))
        cf_dict = self.control_flow_stream_stack.pop()
        self.control_flow_node_stack.pop()
        self.stream_stack_key.pop()
        if next_label is not None:
            self.__add_to_code_stream(instruction=f'j {end_label}', label=next_label, comment_text='% add intermediate jump to prevent conflicting labels', comment_position='inline')
        for i, line in enumerate([f'begin {cf_label}'] + cf_dict['while'] + cf_dict['then']):
            if i == 0:
                # add visual break
                line = CodeGenerator.__format_visual_break(line, use_indent=True)
            self.__add_to_code_stream(line, add_label=False)
        self.registers.push(reg)
        self.next_label = end_label

    def __read(self, node: Read):
        val_reg = self.registers.pop()
        buf_reg = self.registers.pop()
        stack_instr = f'addi r14,r14,-{self.current_scope.req_mem}'
        comment = '% increment stack frame'
        self.__add_to_code_stream(stack_instr, comment_text=comment, comment_position='inline')
        instr = f'addi {buf_reg},r0,buf'
        comment = '% load address of buffer on stack frame'
        self.__add_to_code_stream(instr, comment_text=comment, comment_position='inline')
        self.__store_word('-8(r14)', buf_reg, comment=comment)
        self.__add_to_code_stream('jl r15,getstr', comment_text='% jump to getstr subroutine', comment_position='inline')
        self.__add_to_code_stream('jl r15,strint', comment_text='% jump to strint subroutine', comment_position='inline')
        use_temp = node.var.temp_var is not None
        stack_instr = f'subi r14,r14,-{self.current_scope.req_mem}'
        comment = '% decrement stack frame'
        self.__add_to_code_stream(stack_instr, comment_text=comment, comment_position='inline')
        # load VARIABLE location
        self.__load_word(node.var, val_reg)
        # then load the variable
        self.__store_word(f'0({val_reg})', 'r13', use_temp=use_temp)
        self.registers.push(val_reg)
        self.registers.push(buf_reg)

    def __write(self, node: Write):

        val_reg = self.registers.pop()
        buf_reg = self.registers.pop()
        eol_reg = self.registers.pop()
        use_temp = node.expr.temp_var is not None
        self.__load_word(node.expr, val_reg, use_temp=use_temp)
        stack_instr = f'addi r14,r14,-{self.current_scope.req_mem}'
        comment = '% increment stack frame'
        self.__add_to_code_stream(stack_instr, comment_text=comment, comment_position='inline')
        self.__store_word('-8(r14)', val_reg, comment='% put value to print on stack frame')
        instr = f'addi {buf_reg},r0,buf'
        comment = '% put address of buffer on stack frame'
        self.__add_to_code_stream(instr, comment_text=comment, comment_position='inline')
        self.__store_word('-12(r14)', buf_reg, comment=comment)
        instr = 'jl r15,intstr'
        self.__add_to_code_stream(instr, comment_text='% jump to intstr subroutine', comment_position='inline')
        self.__store_word('-8(r14)', 'r13', comment='% put result on stack for putstr')
        self.__add_to_code_stream('jl r15,putstr', comment_text='% jump to putstr subroutine', comment_position='inline')
        stack_instr = f'subi r14,r14,-{self.current_scope.req_mem}'
        self.__add_to_code_stream(stack_instr, comment_text='% decrement stack frame', comment_position='inline')
        self.__add_to_code_stream(f'addi {eol_reg},r0,10', comment_text='% load EOL char', comment_position='inline')
        self.__add_to_code_stream(f'putc {eol_reg}', comment_text='% print new line', comment_position='inline')
        self.registers.push(buf_reg)
        self.registers.push(val_reg)
        self.registers.push(eol_reg)

        """
        val_reg = self.registers.pop()
        use_temp = node.expr.temp_var is not None
        self.__load_word(node.expr, val_reg, use_temp=use_temp)
        self.__add_to_code_stream(f'putc {val_reg}', comment_text='% print the value', comment_position='inline')
        """

    def __store_word(self, left_op: Union[str, AbstractSyntaxNode], register: str, use_temp: bool = True, comment: str = None, req_intermediate: bool = False):
        if isinstance(left_op, AbstractSyntaxNode):
            if req_intermediate and isinstance(left_op, Var) and left_op.temp_var is not None:
                inter_reg = self.registers.pop()
                self.__add_to_code_stream(f'lw {inter_reg},{self.__get_var_offset_str(left_op.temp_var)}')
                offset = f'0({inter_reg})'
                comment = f'% store value in {left_op.temp_var.name}'
                self.registers.push(inter_reg)
            else:
                var = left_op.temp_var if use_temp else left_op.sem_rec
                offset = self.__get_var_offset_str(var)
                comment = f'% store value in {var.name}'
        else:
            offset = left_op
        instr = f'sw {offset},{register}'
        self.__add_to_code_stream(instr, comment_text=comment, comment_position='inline')

    def __load_word(self, node: AbstractSyntaxNode, register: str, use_temp: bool = True):
        if node.temp_var is not None and node.temp_var.from_var:
            # have to load the variable address first
            inter_reg = self.registers.pop()
            self.__add_to_code_stream(f'lw {inter_reg},{self.__get_var_offset_str(node.temp_var)}')
            offset = f'0({inter_reg})'
            var = node.temp_var
        else:
            var = node.temp_var if use_temp else node.sem_rec
            offset = self.__get_var_offset_str(var)
        instr = f'lw {register},{offset}'
        comment = f'% load value for {var.name}'
        self.__add_to_code_stream(instr, comment_text=comment, comment_position='inline')
        if node.temp_var is not None and node.temp_var.from_var:
            self.registers.push(inter_reg)

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
        self.__store_word(store_node, temp_reg, use_temp=use_temp, req_intermediate=True)
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
    def __format_visual_break(comment_text, use_indent: bool = False) -> str:
        if use_indent:
            ident_beg = " " * CodeGenerator.max_indent
        else:
            ident_beg = ""
        beg = f'{ident_beg}%  ====== {comment_text} '
        return f'{beg}{"=" * (CodeGenerator.req_comment_len - len(beg))}'

    def __reserve_variable_memory(self, node: AbstractSyntaxNode):
        res_comment = f'% Reserve space for variable {node.sem_rec.name}'
        self.__add_to_data_stream(node.sem_rec.memory_size, comment_text=res_comment, comment_position='inline')
