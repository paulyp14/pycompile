from typing import Type

from pycompile.lex.token import *
from pycompile.parser.strategy.strategy import ParsingStrategy


class RecursiveDescentParser(ParsingStrategy):

    def _parse(self):
        self.set_lookahead()

        if self.start() and self.match("$"):
            self.success = True

    def match(self, expected: str) -> bool:
        matched = False
        if self.lookahead.lexeme == expected:
            matched = True
        self.move()
        return matched

    def token_match(self, expected: Type[Token]):
        matched = False
        if isinstance(self.lookahead, expected):
            matched = True
        self.move()
        return matched

    def next_is(self, expected: Type[Token]):
        return isinstance(self.lookahead, expected)

    def start(self) -> bool:
        if self.next() in ['main', 'class', 'func']:
            if self.prog():
                self.rules.append('<START> ::= <prog>')
                return True
            else:
                return False
        else:
            return False

    def prog(self) -> bool:
        if self.next() in ['main', 'class', 'func']:
            if self.rept_prog0() and self.rept_prog1() and self.match('main') and self.func_body():
                self.rules.append("<prog> ::= <rept-prog0> <rept-prog1> 'main' <funcBody>")
                return True
            else:
                return False
        else:
            return False

    def rept_prog0(self) -> bool:
        if self.next() == 'class':
            if self.class_decl() and self.rept_prog0():
                self.rules.append('<rept-prog0> ::= <classDecl> <rept-prog0>')
                return True
            else:
                return False
        elif self.next() in ['main', 'func']:
            self.rules.append('<rept-prog0> ::= EPSILON')
            return True
        else:
            return False

    def rept_prog1(self) -> bool:
        if self.next() == 'func':
            if self.func_def() and self.rept_prog1():
                self.rules.append('<rept-prog1> ::= <funcDef> <rept-prog1>')
                return True
            else:
                return False
        elif self.next() == 'main':
            self.rules.append('<rept-prog1> ::= EPSILON')
            return True
        else:
            return False

    def array_size(self) -> bool:
        if self.next() == '[':
            if self.match('[') and self.array_size_end():
                self.rules.append("<arraySize> ::= '[' <arraySizeEnd>")
                return True
            else:
                return False
        else:
            return False

    def array_size_end(self) -> bool:
        if self.next_is(Integer):
            if self.token_match(Integer) and self.match(']'):
                self.rules.append("<arraySizeEnd> ::=  'intNum' ']'")
                return True
            else:
                return False
        elif self.next() == ']':
            if self.match(']'):
                self.rules.append("<arraySizeEnd> ::=  ']'")
                return True
            else:
                return False
        else:
            return False

    def func_decl(self):
        if self.next() == 'func':
            if (
                    self.match('func') and
                    self.token_match(Id) and
                    self.match('(') and
                    self.f_params() and
                    self.match(')') and
                    self.func_mid() and
                    self.match(';')
            ):
                self.rules.append("<funcDecl> ::= 'func' 'id' '(' <fParams> ')' <funcMid> ';'")
                return True
            else:
                return False
        else:
            return False

    def func_def(self) -> bool:
        if self.next() == 'func':
            if self.func_head() and self.func_body():
                self.rules.append("<funcDef> ::= <funcHead> <funcBody>")
                return True
            else:
                return False
        else:
            return False

    def func_head(self) -> bool:
        if self.next() == 'func':
            if (
                self.match('func') and
                self.opt_func_head1() and
                self.match('(') and
                self.f_params() and
                self.match(')') and
                self.func_mid()
            ):
                self.rules.append("<funcHead> ::= 'func' <opt-funcHead1> '(' <fParams> ')' <funcMid>")
                return True
            else:
                return False
        else:
            return True

    def opt_func_head1(self) -> bool:
        if self.next_is(Id):
            if self.token_match(Id) and self.opt_func_head_end():
                self.rules.append("<opt-funcHead1> ::= 'id' <opt-funcHeadEnd>")
                return True
            else:
                return False
        else:
            return False

    def opt_func_head_end(self) -> bool:
        if self.next() == "::":
            if self.match("::") and self.token_match(Id):
                self.rules.append("<opt-funcHeadEnd> ::= 'sr' 'id'")
                return True
            else:
                return False
        elif self.next() == '(':
            self.rules.append("<opt-funcHeadEnd> ::= EPSILON")
            return True
        else:
            return False

    def f_params(self) -> bool:
        if self.next() in ['integer', 'float', 'string'] or self.next_is(Id):
            if self.type() and self.token_match(Id) and self.rept_f_params2() and self.rept_f_params3():
                self.rules.append("<fParams> ::= <type> 'id' <rept-fParams2> <rept-fParams3>")
                return True
            else:
                return False
        elif self.next() == ')':
            self.rules.append('<fParams> ::= EPSILON')
            return True
        else:
            return False

    def rept_f_params2(self) -> bool:
        if self.next() == '[':
            if self.array_size() and self.rept_f_params2():
                self.rules.append('<rept-fParams2> ::= <arraySize> <rept-fParams2>')
                return True
            else:
                return False
        elif self.next() in [')', ',']:
            self.rules.append('<rept-fParams2> ::= EPSILON')
            return True
        else:
            return False

    def rept_f_params3(self) -> bool:
        if self.next() == ',':
            if self.f_params_tail() and self.rept_f_params3():
                self.rules.append('<rept-fParams3> ::= <fParamsTail> <rept-fParams3>')
                return True
            else:
                return False
        elif self.next() == ')':
            self.rules.append('<rept-fParams3> ::= EPSILON')
            return True
        else:
            return False

    def f_params_tail(self) -> bool:
        if self.next() == ',':
            if self.match(',') and self.type() and self.token_match(Id) and self.rept_f_params_tail3():
                self.rules.append("<fParamsTail> ::= ',' <type> 'id' <rept-fParamsTail3>")
                return True
            else:
                return False
        else:
            return False

    def rept_f_params_tail3(self) -> bool:
        if self.next() == '[':
            if self.array_size() and self.rept_f_params_tail3():
                self.rules.append("<rept-fParamsTail3> ::= <arraySize> <rept-fParamsTail3>")
                return True
            else:
                return False
        elif self.next() in [',', ')']:
            self.rules.append('<rept-fParamsTail3> ::= EPSILON')
            return True
        else:
            return False

    def func_mid(self) -> bool:
        if self.next() == ":":
            if self.match(":") and self.func_end():
                self.rules.append("<funcMid> ::= ':' <funcEnd>")
                return True
            else:
                return False
        else:
            return False

    def func_end(self) -> bool:
        if self.next() == 'void':
            if self.match('void'):
                self.rules.append("<funcEnd> ::= 'void'")
                return True
            else:
                return False
        elif self.next() in ['integer', 'float', 'string'] or self.next_is(Id):
            if self.type():
                self.rules.append('<funcEnd> ::= <type>')
                return True
            else:
                return False
        else:
            return False

    def func_body(self) -> bool:
        if self.next() == '{':
            if self.match('{') and self.opt_func_body1() and self.rept_func_body2() and self.match('}'):
                self.rules.append("<funcBody> ::= '{' <opt-funcBody1> <rept-funcBody2> '}'")
                return True
            else:
                return False
        else:
            return False

    def opt_func_body1(self) -> bool:
        if self.next() == 'var':
            if self.match('var') and self.match('{') and self.rept_opt_func_body12() and self.match('}'):
                self.rules.append("<opt-funcBody1> ::= 'var' '{' <rept-opt-funcBody12> '}'")
                return True
            else:
                return False
        elif self.next() in ['if', 'while', 'read', 'write', 'return', 'break', 'continue', '{'] or self.next_is(Id):
            self.rules.append('<opt-funcBody1> ::= EPSILON')
            return True
        else:
            return False

    def rept_func_body2(self) -> bool:
        if self.next() in ['if', 'while', 'read', 'write', 'return', 'break', 'continue'] or self.next_is(Id):
            if self.statement() and self.rept_func_body2():
                self.rules.append("<rept-funcBody2> ::= <statement> <rept-funcBody2>")
                return True
            else:
                return False
        elif self.next() == '}':
            self.rules.append('<rept-funcBody2> ::= EPSILON')
            return True
        else:
            return False

    def rept_opt_func_body12(self) -> bool:
        if self.next() in ['integer', 'float', 'string'] or self.next_is(Id):
            if self.var_decl() and self.rept_opt_func_body12():
                self.rules.append('<rept-opt-funcBody12> ::= <varDecl> <rept-opt-funcBody12>')
                return True
            else:
                return False
        elif self.next() == '}':
            self.rules.append('<rept-opt-funcBody12> ::= EPSILON')
            return True
        else:
            return False

    def class_decl(self) -> bool:
        if self.next() == 'class':
            if (
                    self.match('class') and
                    self.token_match(Id) and
                    self.opt_class_decl2() and
                    self.match('{') and
                    self.rept_class_decl4() and
                    self.match('}') and
                    self.match(';')
            ):
                self.rules.append("<classDecl> ::= 'class' 'id' <opt-classDecl2> '{' <rept-classDecl4> '}' ';'")
                return True
            else:
                return False
        else:
            return False

    def opt_class_decl2(self) -> bool:
        if self.next() == 'inherits':
            if self.match('inherits') and self.token_match(Id) and self.rept_opt_class_decl22():
                self.rules.append("<opt-classDecl2> ::= 'inherits' 'id' <rept-opt-classDecl22>")
                return True
            else:
                return False
        elif self.next() == '{':
            self.rules.append("<opt-classDecl2> ::= EPSILON")
            return True
        else:
            return False

    def rept_opt_class_decl22(self) -> bool:
        if self.next() == ',':
            if self.match(',') and self.token_match(Id) and self.rept_opt_class_decl22():
                self.rules.append("<rept-opt-classDecl22> ::= ',' 'id' <rept-opt-classDecl22>")
                return True
            else:
                return False
        elif self.next() == '{':
            self.rules.append("<rept-opt-classDecl22> ::= EPSILON")
            return True
        else:
            return False

    def rept_class_decl4(self) -> bool:
        if self.next() in ['public', 'private', 'func', 'integer', 'float', 'string'] or self.next_is(Id):
            if self.visibility() and self.member_decl() and self.rept_class_decl4():
                self.rules.append('<rept-classDecl4> ::= <visibility> <memberDecl> <rept-classDecl4>')
                return True
            else:
                return False
        elif self.next() == '}':
            self.rules.append('<rept-classDecl4> ::= EPSILON')
            return True
        else:
            return False

    def member_decl(self) -> bool:
        if self.next() in ['integer', 'float', 'string'] or self.next_is(Id):
            if self.var_decl():
                self.rules.append('<memberDecl> ::= <varDecl>')
                return True
            else:
                return False
        elif self.next() == 'func':
            if self.func_decl():
                self.rules.append('<memberDecl> ::= <funcDecl>')
                return True
            else:
                return False
        else:
            return False

    def statement(self) -> bool:
        if self.next() == 'if':
            if (
                    self.match('if') and
                    self.match('(') and
                    self.rel_expr() and
                    self.match(')') and
                    self.match('then') and
                    self.stat_block() and
                    self.match('else') and
                    self.stat_block() and
                    self.match(';')
            ):
                self.rules.append("<statement> ::= 'if' '(' <relExpr> ')' 'then' <statBlock> 'else' <statBlock> ';'")
                return True
            else:
                return False
        elif self.next() == 'while':
            if (
                    self.match('while') and
                    self.match('(') and
                    self.rel_expr() and
                    self.match(')') and
                    self.stat_block() and
                    self.match(';')
            ):
                self.rules.append("<statement> ::= 'while' '(' <relExpr> ')' <statBlock> ';'")
                return True
            else:
                return False
        elif self.next() == 'read':
            if self.match('read') and self.match('(') and self.stat_variable() and self.match(';'):
                self.rules.append("<statement> ::= 'read' '(' <statVariable> ';'")
                return True
            else:
                return False
        elif self.next() == 'write':
            if self.match('write') and self.match('(') and self.expr() and self.match(')') and self.match(';'):
                self.rules.append("<statement> ::= 'write' '(' <expr> ')' ';'")
                return True
            else:
                return False
        elif self.next() == 'return':
            if self.match('return') and self.match('(') and self.expr() and self.match(')') and self.match(';'):
                self.rules.append("<statement> ::= 'return' '(' <expr> ')' ';'")
                return True
            else:
                return False
        elif self.next() == 'break':
            if self.match('break') and self.match(';'):
                self.rules.append("<statement> ::= 'break' ';'")
                return True
            else:
                return False
        elif self.next() == 'continue':
            if self.match('continue') and self.match(';'):
                self.rules.append("<statement> ::= 'continue' ';'")
                return True
            else:
                return False
        elif self.next_is(Id):
            if self.assign_func_start() and self.match(';'):
                self.rules.append("<statement> ::= <assignFuncStart> ';'")
                return True
            else:
                return False
        else:
            return False

    def stat_block(self):
        if self.next() == '{':
            if self.match('{') and self.rept_stat_block1() and self.match('}'):
                self.rules.append("<statBlock> ::= '{' <rept-statBlock1> '}'")
                return True
            else:
                return False
        elif self.next() in ['if', 'while', 'read', 'write', 'return', 'break','continue'] or self.next_is(Id):
            if self.statement():
                self.rules.append('<statBlock> ::= <statement>')
                return True
            else:
                return False
        elif self.next() in ['else', 'semi']:
            self.rules.append('<statBlock> ::= EPSILON')
            return True
        else:
            return False

    def sign(self):
        if self.next() == '+':
            if self.match('+'):
                self.rules.append("<sign> ::= '+'")
                return True
            else:
                return False
        elif self.next() == '-':
            if self.match('-'):
                self.rules.append("<sign> ::= '-'")
                return True
            else:
                return False
        else:
            return False

    def rept_stat_block1(self):
        if self.next() in ['if', 'while', 'read', 'write', 'return', 'break', 'continue'] or self.next_is(Id):
            if self.statement() and self.rept_stat_block1():
                self.rules.append('<rept-statBlock1> ::= <statement> <rept-statBlock1>')
                return True
            else:
                return False
        elif self.next() == '}':
            self.rules.append('<rept-statBlock1> ::= EPSILON')
            return True
        return False


    def stat_variable(self):
        if self.next_is(Id):
            if self.token_match(Id) and self.stat_var_rept() and self.stat_var_end():
                self.rules.append("<statVariable> ::= 'id' <statVarRept> <statVarEnd>")
                return True
            else:
                return False
        else:
            return False

    def stat_var_rept(self):
        if self.next() ==  '(':
            if self.match('(') and self.a_params() and self.match(')') and self.match('.') and self.stat_var_rept2():
                self.rules.append("<statVarRept> ::= '(' <aParams> ')' '.' <statVarRept2>")
                return True
            else:
                return False
        elif self.next() in ['[', '.', ')']:
            if self.indice_rept():
                self.rules.append("<statVarRept> ::= <indiceRept>")
                return True
            else:
                return False
        else:
            return False

    def stat_var_rept2(self):
        if self.next_is(Id):
            if self.token_match(Id) and self.stat_var_rept():
                self.rules.append("<statVarRept2> ::= 'id' <statVarRept>")
                return True
            else:
                return False
        else:
            return False

    def indice_rept(self):
        if self.next() == '[':
            if self.match('[') and self.arith_expr_no_rel() and self.match(']') and self.indice_rept():
                self.rules.append("<indiceRept> ::= '[' <arithExprNoRel> ']' <indiceRept>")
                return True
            else:
                return False
        elif self.next() == '.':
            if self.match('.') and self.stat_var_rept2():
                self.rules.append("<indiceRept> ::= '.' <statVarRept2>")
                return True
            else:
                return False
        elif self.next() == ')':
            if self.match(')'):
                self.rules.append("<indiceRept> ::= ')'")
                return True
            else:
                return False
        else:
            return False

    def stat_var_end(self):
        if self.next() == '[':
            if self.match('[') and self.arith_expr_no_rel() and self.match(']') and self.stat_var_end():
                self.rules.append("<statVarEnd> ::= '[' <arithExprNoRel> ']' <statVarEnd>")
                return True
            else:
                return False
        elif self.next() == ';':
            self.rules.append("<statVarEnd> ::= EPSILON")
            return True
        else:
            return False

    def type(self) -> bool:
        if self.next() == 'float':
            if self.match('float'):
                self.rules.append("<type> ::= 'float'")
                return True
            else:
                return False
        elif self.next() == 'integer':
            if self.match('integer'):
                self.rules.append("<type> ::= 'integer'")
                return True
            else:
                return False
        elif self.next() == 'string':
            if self.match('string'):
                self.rules.append("<type> ::= 'string'")
                return True
            else:
                return False
        elif self.next_is(Id):
            if self.token_match(Id):
                self.rules.append("<type> ::= 'id'")
                return True
            else:
                return False
        else:
            return False

    def var_decl(self) -> bool:
        if self.next() in ['float', 'integer', 'string'] or self.next_is(Id):
            if self.type() and self.token_match(Id) and self.rept_var_decl2() and self.match(';'):
                self.rules.append("<varDecl> ::= <type> 'id' <rept-varDecl2> ';'")
                return True
            else:
                return False
        else:
            return False

    def rept_var_decl2(self) -> bool:
        if self.next() == '[':
            if self.array_size() and self.rept_var_decl2():
                self.rules.append('<rept-varDecl2> ::= <arraySize> <rept-varDecl2>')
                return True
            else:
                return False
        elif self.next() == ';':
            self.rules.append('<rept-varDecl2> ::= EPSILON')
            return True
        else:
            return False

    def rept_variable2(self):
        if self.next() == '[':
            if self.indice() and self.rept_variable2():
                self.rules.append("<rept-variable2> ::= <indice> <rept-variable2>")
                return True
            else:
                return False
        elif self.next() in [';', '[', '.', '=', '*', '/', '&', '+', '-', '|', '==', '<>', '<', '>', '<=', '>=', ',', ':', ']', ')']:
            self.rules.append('<rept-variable2> ::= EPSILON')
            return True
        else:
            return False

    def visibility(self) -> bool:
        if self.next() == 'public':
            if self.match('public'):
                self.rules.append("<visibility> ::= 'public'")
                return True
            else:
                return False
        elif self.next() == 'private':
            if self.match('private'):
                self.rules.append("<visibility> ::= 'private'")
                return True
            else:
                return False
        elif self.next() in ['func', 'integer', 'float', 'string'] or self.next_is(Id):
            self.rules.append("<visibility> ::= EPSILON")
            return True
        else:
            return False

    def rept_idnest1(self):
        if self.next() == '[':
            if self.indice() and self.rept_idnest1():
                self.rules.append("<rept-idnest1> ::= <indice> <rept-idnest1>")
                return True
            else:
                return False
        elif self.next() == '.':
            self.rules.append("<rept-idnest1> ::= EPSILON")
            return True
        else:
            return False

    def rept_a_params1(self):
        if self.next() == ',':
            if self.a_params_tail() and self.rept_a_params1():
                self.rules.append("<rept-aParams1> ::= <aParamsTail> <rept-aParams1>")
                return True
            else:
                return False
        elif self.next() == ')':
            self.rules.append("<rept-aParams1> ::= EPSILON")
            return True
        else:
            return False

    def rel_op(self):
        if self.next() == '==':
            if self.match('=='):
                self.rules.append("<relOp> ::= 'eq'")
                return True
            else:
                return False
        elif self.next() == '<>':
            if self.match('<>'):
                self.rules.append("<relOp> ::= 'neq'")
                return True
            else:
                return False
        elif self.next() == '>':
            if self.match('>'):
                self.rules.append("<relOp> ::= 'gt'")
                return True
            else:
                return False
        elif self.next() == '<':
            if self.match('<'):
                self.rules.append("<relOp> ::= 'lt'")
                return True
            else:
                return False
        elif self.next() == '<=':
            if self.match('<='):
                self.rules.append("<relOp> ::= 'leq'")
                return True
            else:
                return False
        elif self.next() == '>=':
            if self.match('>='):
                self.rules.append("<relOp> ::= 'geq'")
                return True
            else:
                return False
        else:
            return False

    def mult_op(self):
        if self.next() == '*':
            if self.match('*'):
                self.rules.append("<multOp> ::= '*'")
            else:
                return False
        elif self.next() == '/':
            if self.match('/'):
                self.rules.append("<multOp> ::= '/'")
            else:
                return False
        elif self.next() == '&':
            if self.match('&'):
                self.rules.append("<multOp> ::= 'and'")
            else:
                return False

    def indice(self):
        if self.next() == '[':
            if self.match('[') and self.arith_expr_no_rel() and self.match(']'):
                self.rules.append("<indice> ::= '[' <arithExprNoRel> ']'")
                return True
            else:
                return False
        else:
            return False

    def idnest_end(self):
        if self.next() in ['[', '.']:
            if self.rept_idnest1() and self.match('.'):
                self.rules.append("<idnestEnd> ::= <rept-idnest1> '.'")
                return True
            else:
                return False
        elif self.next() == '(':
            if self.match('(') and self.a_params() and self.match(')') and self.match('.'):
                self.rules.append("<idnestEnd> ::= '(' <aParams> ')' '.'")
                return True
            else:
                return False
        else:
            return False

    def assign_func_start(self):
        if self.next_is(Id):
            if self.token_match(Id) and self.func_var_rept2():
                self.rules.append("<assignFuncStart> ::= 'id' <funcVarRept2>")
                return True
            else:
                return False
        else:
            return False

    def func_var_rept2(self):
        if self.next() in ['.', '(', '[']:
            if self.idnest_end() and self.func_var_rept_or_end2():
                self.rules.append("<funcVarRept2> ::= <idNestEnd> <funcVarReptOrEnd2>")
                return True
            else:
                return False
        if self.next() in ['=']:
            if self.assign_op() and self.expr():
                self.rules.append("FUNCVARREPT2 -> ASSIGNOP EXPR  .")
                return True
            else:
                return False
        else:
            return False

    def func_var_rept_or_end2(self):
        if self.next_is(Id):
            if self.token_match(Id) and self.func_var_rept2():
                self.rules.append("<funcVarReptOrEnd2> ::= 'id' <funcVarRept2>")
                return True
            else:
                return False
        elif self.next() == '(':
            if self.function_call():
                self.rules.append("<funcVarReptOrEnd2> ::= <functionCall>")
                return True
            else:
                return False
        elif self.next() == '[':
            if self.variable() and self.assign_op() and self.expr():
                self.rules.append("<funcVarReptOrEnd2> ::= <variable> <assignOp> <expr>")
                return True
            else:
                return False
        else:
            return False

    def func_var_rept1(self):
        if self.next() in ['.', '(', '[']:
            if self.idnest_end() and self.func_var_rept_or_end1():
                self.rules.append("<funcVarRept1> ::= <idNestEnd> <funcVarReptOrEnd1>")
                return True
            else:
                return False
        elif self.next() in [';', '*', '/', '&', '+', '-', '|', '==', '<>', '<', '>', '<=', '>=', ',', ':', ']', ')']:
            self.rules.append('<funcVarRept1> ::= EPSILON')
            return True
        else:
            return False

    def func_var_rept_or_end1(self):
        if self.next_is(Id):
            if self.token_match(Id) and self.func_var_rept2():
                self.rules.append("<funcVarReptOrEnd1> ::= 'id' <funcVarRept1>")
                return True
            else:
                return False
        elif self.next() == '(':
            if self.function_call():
                self.rules.append("<funcVarReptOrEnd1> ::= <functionCall>")
                return True
            else:
                return False
        elif self.next() == '[':
            if self.variable():
                self.rules.append("<funcVarReptOrEnd1> ::= <variable>")
                return True
            else:
                return False
        else:
            return False

    def func_var_start(self):
        if self.next_is(Id):
            if self.token_match(Id) and self.func_var_rept1():
                self.rules.append("<funcVarStart> ::= 'id' <funcVarRept1>")
                return True
            else:
                return False
        else:
            return False

    def variable(self):
        if self.next() == '[':
            if self.rept_variable2():
                self.rules.append("<variable> ::= <rept-variable2>")
                return True
            else:
                return False
        else:
            return False

    def function_call(self):
        if self.next() == '(':
            if self.match('(') and self.a_params() and self.match(')'):
                self.rules.append("<functionCall> ::= '(' <aParams> ')'")
                return True
            else:
                return False
        else:
            return False

    def assign_op(self):
        if self.next() == '=':
            if self.match('='):
                self.rules.append("<assignOp> ::= '='")
                return True
            else:
                return False
        else:
            return False

    def factor(self):
        if self.next_is(Id):
            if self.func_var_start():
                self.rules.append("<factor> ::= <funcVarStart>")
                return True
            else:
                return False
        elif self.next_is(Float):
            if self.token_match(Float):
                self.rules.append("<factor> ::= <floatLit>")
                return True
            else:
                return False
        elif self.next_is(Integer):
            if self.token_match(Integer):
                self.rules.append("<factor> ::= <intLit>")
                return True
            else:
                return False
        elif self.next_is(String):
            if self.token_match(String):
                self.rules.append("<factor> ::= <stringLit>")
                return True
            else:
                return False
        elif self.next() == '(':
            if self.match('(') and self.arith_expr_no_rel() and self.match(')'):
                self.rules.append("<factor> ::= '(' <arithExprNoRel> ')'")
                return True
            else:
                return False
        elif self.next() == '!':
            if self.match('!') and self.factor():
                self.rules.append("<factor> ::= 'not' <factor>")
                return True
            else:
                return False
        elif self.next() in ['+', '-']:
            if self.sign() and self.factor():
                self.rules.append("<factor> ::= <sign> <factor>")
                return True
            else:
                return False
        elif self.next() == '?':
            if (
                    self.match('?') and 
                    self.match('[') and 
                    self.expr() and 
                    self.match(":") and 
                    self.expr() and 
                    self.match(":") and 
                    self.expr() and 
                    self.match(']')
            ):
                self.rules.append("<factor> ::= 'qm' '[' <expr> ':' <expr> ':' <expr> ']'")
                return True
            else:
                return False
        else:
            return False
    
    def factor_no_rel(self):
        if self.next_is(Id):
            if self.func_var_start():
                self.rules.append("<factorNoRel> ::= <funcVarStart>")
                return True
            else:
                return False
        elif self.next_is(Float):
            if self.token_match(Float):
                self.rules.append("<factorNoRel> ::= <floatLit>")
                return True
            else:
                return False
        elif self.next_is(Integer):
            if self.token_match(Integer):
                self.rules.append("<factorNoRel> ::= <intLit>")
                return True
            else:
                return False
        elif self.next_is(String):
            if self.token_match(String):
                self.rules.append("<factorNoRel> ::= <stringLit>")
                return True
            else:
                return False
        elif self.next() == '(':
            if self.match('(') and self.arith_expr_no_rel() and self.match(')'):
                self.rules.append("<factorNoRel> ::= '(' <arithExprNoRel> ')'")
                return True
            else:
                return False
        elif self.next() == '!':
            if self.match('!') and self.factor_no_rel():
                self.rules.append("<factorNoRel> ::= 'not' <factorNoRel>")
                return True
            else:
                return False
        elif self.next() in ['+', '-']:
            if self.sign() and self.factor_no_rel():
                self.rules.append("<factorNoRel> ::= <sign> <factorNoRel>")
                return True
            else:
                return False
        elif self.next() == '?':
            if (
                    self.match('?') and 
                    self.match('[') and 
                    self.expr() and 
                    self.match(":") and 
                    self.expr() and 
                    self.match(":") and 
                    self.expr() and 
                    self.match(']')
            ):
                self.rules.append("<factorNoRel> ::= 'qm' '[' <expr> ':' <expr> ':' <expr> ']'")
                return True
            else:
                return False
        else:
            return False

    def arith_expr_no_rel(self):
        if (
                self.next_is(Id) or
                self.next_is(Float) or
                self.next_is(String) or
                self.next_is(Integer) or
                self.next() in ['+', '-', '?', '!', '(']
        ):
            if self.term_no_rel() and self.right_rec_arith_expr_no_rel():
                self.rules.append("<arithExprNoRel> ::= <termNoRel> <rightrec-arithExprNoRel>")
                return True
            else:
                return False
        else:
            return False

    def right_rec_term_no_rel(self):
        if self.next() in ['/', '*', '&']:
            if self.mult_op() and self.factor_no_rel() and self.right_rec_term_no_rel():
                self.rules.append('<rightrec-termNoRel> ::= <multOp> <factorNoRel> <rightrec-termNoRel>')
                return True
            else:
                return False
        elif self.next() in [';', '+', '-', '|', '==', '<>', '<', '>', '<=', '>=', ',', ':', ']', ')']:
            self.rules.append('<rightrec-termNoRel> ::= EPSILON')
            return True
        else:
            return False

    def right_rec_arith_expr_no_rel(self):
        if self.next() in ['+', '-', '|']:
            if self.add_op() and self.term_no_rel() and self.right_rec_arith_expr_no_rel():
                self.rules.append('<rightrec-arithExprNoRel> ::= <addOp> <termNoRel> <rightrec-arithExprNoRel>')
                return True
            else:
                return False
        elif self.next() in [';', '==', '<>', '<', '>', '<=', '>=', ',', ':', ']', ')']:
            self.rules.append('<rightrec-arithExprNoRel> ::= EPSILON')
            return True
        else:
            return False

    def right_rec_arith_expr(self):
        if self.next() in ['+', '-', '|']:
            if self.add_op() and self.term() and self.right_rec_arith_expr():
                self.rules.append('<rightrec-arithExpr> ::= <addOp> <term> <rightrec-arithExpr>')
                return True
            else:
                return False
        elif self.next() in ['==', '<>', '<', '>', '<=', '>=']:
            if self.rel_op() and self.term_no_rel() and self.right_rec_arith_expr_no_rel():
                self.rules.append("<rightrec-arithExpr> ::= <relOp> <termNoRel> <rightrec-arithExprNoRel>")
                return True
            else:
                return False
        elif self.next() in [';', ',', ':', ']', ')']:
            self.rules.append('<rightrec-arithExpr> ::= EPSILON')
            return True
        else:
            return False

    def rel_expr(self):
        if (
                self.next_is(Id) or
                self.next_is(Float) or
                self.next_is(String) or
                self.next_is(Integer) or
                self.next() in ['+', '-', '?', '!', '(']
        ):
            if self.arith_expr_no_rel() and self.rel_op() and self.arith_expr_no_rel():
                self.rules.append("<relExpr> ::= <arithExprNoRel> <relOp> <arithExprNoRel>")
                return True
            else:
                return False
        else:
            return False

    def expr(self):
        if (
                self.next_is(Id) or
                self.next_is(Float) or
                self.next_is(String) or
                self.next_is(Integer) or
                self.next() in ['+', '-', '?', '!', '(']
        ):
            if self.arith_expr():
                self.rules.append("<expr> ::= <arithExpr>")
                return True
            else:
                return False
        else:
            return False

    def term_no_rel(self):
        if (
                self.next_is(Id) or
                self.next_is(Float) or
                self.next_is(String) or
                self.next_is(Integer) or
                self.next() in ['+', '-', '?', '!', '(']
        ):
            if self.factor_no_rel() and self.right_rec_term_no_rel():
                self.rules.append("<termNoRel> ::= <factorNoRel> <rightrec-termNoRel>")
                return True
            else:
                return False
        else:
            return False

    def term(self):
        if (
                self.next_is(Id) or
                self.next_is(Float) or
                self.next_is(String) or
                self.next_is(Integer) or
                self.next() in ['+', '-', '?', '!', '(']
        ):
            if self.factor() and self.right_rec_term_no_rel():
                self.rules.append("<term> ::= <factor> <rightrec-termNoRel>")
                return True
            else:
                return False
        else:
            return False

    def arith_expr(self):
        if (
                self.next_is(Id) or
                self.next_is(Float) or
                self.next_is(String) or
                self.next_is(Integer) or
                self.next() in ['+', '-', '?', '!', '(']
        ):
            if self.term() and self.right_rec_arith_expr():
                self.rules.append("<arithExpr> ::= <term> <rightrec-arithExpr>")
                return True
            else:
                return False
        else:
            return False

    def a_params_tail(self):
        if self.next() == ',':
            if self.match(',') and self.expr():
                self.rules.append("<aParamsTail> ::= ',' <expr>")
                return True
            else:
                return False
        else:
            return False

    def a_params(self):
        if (
                self.next_is(Id) or
                self.next_is(Float) or
                self.next_is(String) or
                self.next_is(Integer) or
                self.next() in ['+', '-', '?', '!', '(']
        ):
            if self.expr() and self.rept_a_params1():
                self.rules.append("<aParams> ::= <expr> <rept-aParams1>")
                return True
            else:
                return False
        elif self.next() == ')':
            self.rules.append("<aParams> ::= EPSILON")
            return True
        else:
            return False

    def add_op(self):
        if self.next() == '+':
            if self.match('+'):
                self.rules.append("<addOp> ::= '+'")
                return True
            else:
                return False
        elif self.next() == '-':
            if self.match('-'):
                self.rules.append("<addOp> ::= '-'")
                return True
            else:
                return False
        elif self.next() == '|':
            if self.match('|'):
                self.rules.append("<addOp> ::= '|'")
                return True
            else:
                return False
        else:
            return False
