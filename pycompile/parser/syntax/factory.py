from typing import Union, Tuple, Type

from pycompile.lex.token import *
from pycompile.utils.stack import Stack
from pycompile.parser.syntax.node import *


class AbstractSyntaxNodeFactory:

    # create map between semantic actions and factory methods
    ACTION_MAP = {
        'make-leaf': lambda **kwargs: AbstractSyntaxNodeFactory.create_leaf(**kwargs),
        'make-emptyLeaf': lambda **kwargs: AbstractSyntaxNodeFactory.create_empty_leaf(**kwargs),
        'make-operator': lambda **kwargs: AbstractSyntaxNodeFactory.create_operator(**kwargs),
        'push-op': lambda **kwargs: AbstractSyntaxNodeFactory.push_op(**kwargs),
        'make-term': lambda **kwargs: AbstractSyntaxNodeFactory.create_term(**kwargs),
        'make-factor': lambda **kwargs: AbstractSyntaxNodeFactory.create_factor(**kwargs),
        'make-arithExp': lambda **kwargs: AbstractSyntaxNodeFactory.create_arith_expr(**kwargs),
        'make-expr': lambda **kwargs: AbstractSyntaxNodeFactory.create_expr(**kwargs),
        'push-unary': lambda **kwargs: AbstractSyntaxNodeFactory.push_op(**kwargs),
        'make-negation': lambda **kwargs: AbstractSyntaxNodeFactory.create_negation(**kwargs),
        'make-signed': lambda **kwargs: AbstractSyntaxNodeFactory.create_signed(**kwargs),
        'make-BREAK': lambda **kwargs: AbstractSyntaxNodeFactory.create_break(**kwargs),
        'make-CONTINUE': lambda **kwargs: AbstractSyntaxNodeFactory.create_continue(**kwargs),
        'make-IF': lambda **kwargs: AbstractSyntaxNodeFactory.create_if(**kwargs),
        'make-WHILE': lambda **kwargs: AbstractSyntaxNodeFactory.create_while(**kwargs),
        'make-READ': lambda **kwargs: AbstractSyntaxNodeFactory.create_read(**kwargs),
        'make-WRITE': lambda **kwargs: AbstractSyntaxNodeFactory.create_write(**kwargs),
        'make-RETURN': lambda **kwargs: AbstractSyntaxNodeFactory.create_return(**kwargs),
        'make-Prog': lambda **kwargs: AbstractSyntaxNodeFactory.create_prog(**kwargs),
        'make-classList': lambda **kwargs: AbstractSyntaxNodeFactory.create_class_list(**kwargs),
        'make-membList': lambda **kwargs: AbstractSyntaxNodeFactory.create_member_list(**kwargs),
        'make-funcDL': lambda **kwargs: AbstractSyntaxNodeFactory.create_func_list(**kwargs),
        'make-indList': lambda **kwargs: AbstractSyntaxNodeFactory.create_idx_list(**kwargs),
        'make-classDecl': lambda **kwargs: AbstractSyntaxNodeFactory.create_class(**kwargs),
        'make-inherList': lambda **kwargs: AbstractSyntaxNodeFactory.create_inherit_list(**kwargs),
        'make-varDecl': lambda **kwargs: AbstractSyntaxNodeFactory.create_member_var(**kwargs),
        'make-funcDecl': lambda **kwargs: AbstractSyntaxNodeFactory.create_member_func(**kwargs),
        'make-arSep': lambda **kwargs: AbstractSyntaxNodeFactory.add_sep(**kwargs),
        'make-fPList': lambda **kwargs: AbstractSyntaxNodeFactory.create_f_param_list(**kwargs),
        'make-fParam': lambda **kwargs: AbstractSyntaxNodeFactory.create_f_param(**kwargs),
        'make-aRList': lambda **kwargs: AbstractSyntaxNodeFactory.create_dim_list(**kwargs),
        'make-aPList': lambda **kwargs: AbstractSyntaxNodeFactory.create_a_param_list(**kwargs),
        'make-varDList': lambda **kwargs: AbstractSyntaxNodeFactory.create_var_list(**kwargs),
        'make-stat': lambda **kwargs: AbstractSyntaxNodeFactory.create_statement(**kwargs),
        'make-statList': lambda **kwargs: AbstractSyntaxNodeFactory.create_statement_list(**kwargs),
        'make-funcBody': lambda **kwargs: AbstractSyntaxNodeFactory.create_func_body(**kwargs),
        'make-var': lambda **kwargs: AbstractSyntaxNodeFactory.create_var(**kwargs),
        'make-funcDef': lambda **kwargs: AbstractSyntaxNodeFactory.create_func(**kwargs),
        'make-vis': lambda **kwargs: AbstractSyntaxNodeFactory.add_vis(**kwargs),
        'make-sr': lambda **kwargs: AbstractSyntaxNodeFactory.add_sr(**kwargs),
        'make-tern': lambda **kwargs: AbstractSyntaxNodeFactory.make_tern(**kwargs),
    }

    @staticmethod
    def create(semantic_symbol: str, token: Token, last_token: Token, semantic_stack: Stack) -> AbstractSyntaxNode:
        as_kwargs = {
            'semantic_symbol': semantic_symbol,
            'token': token,
            'last_token': last_token,
            'semantic_stack': semantic_stack
        }
        if semantic_symbol in AbstractSyntaxNodeFactory.ACTION_MAP.keys():
            return AbstractSyntaxNodeFactory.ACTION_MAP[semantic_symbol](**as_kwargs)
        else:
            return semantic_symbol

    @staticmethod
    def create_leaf(**kwargs) -> AbstractSyntaxNode:
        return Leaf(token=kwargs.get('last_token'))

    @staticmethod
    def create_empty_leaf(**kwargs) -> AbstractSyntaxNode:
        return Leaf(token=Placeholder('PLACEHOLDER'))

    @staticmethod
    def create_operator(**kwargs):
        stack: Stack = kwargs.get('semantic_stack')
        kwargs['right_operand']: AbstractSyntaxNode = stack.pop()
        kwargs['operator']: str = stack.pop()
        kwargs['left_operand']: AbstractSyntaxNode = stack.pop()
        return Operator(**kwargs)

    @staticmethod
    def push_op(**kwargs):
        token: Token = kwargs.get('last_token')
        return token.lexeme

    @staticmethod
    def create_term(**kwargs):
        kwargs['factor'] = kwargs.get('semantic_stack').pop()
        return Term(**kwargs)

    @staticmethod
    def create_factor(**kwargs):
        kwargs['child'] = kwargs.get('semantic_stack').pop()
        return Factor(**kwargs)

    @staticmethod
    def create_expr(**kwargs):
        kwargs['arith_expr'] = kwargs.get('semantic_stack').pop()
        # TODO, determine if need to look back and see if there is also a rel op... <exprTail>
        return Expr(**kwargs)

    @staticmethod
    def create_arith_expr(**kwargs):
        kwargs['term'] = kwargs.get('semantic_stack').pop()
        return ArithExpr(**kwargs)

    @staticmethod
    def create_negation(**kwargs):
        stack: Stack = kwargs.get('semantic_stack')
        kwargs['factor'] = stack.pop()
        stack.pop()
        kwargs['op'] = stack.pop()
        return Negation(**kwargs)

    @staticmethod
    def create_signed(**kwargs):
        stack: Stack = kwargs.get('semantic_stack')
        kwargs['factor'] = stack.pop()
        kwargs['op'] = stack.pop()
        return Signed(**kwargs)

    @staticmethod
    def create_break(**kwargs) -> AbstractSyntaxNode:
        return Break(token=kwargs.get('last_token'))

    @staticmethod
    def create_continue(**kwargs) -> AbstractSyntaxNode:
        return Continue(token=kwargs.get('last_token'))

    @staticmethod
    def create_if(**kwargs) -> AbstractSyntaxNode:
        stack: Stack = kwargs.get('semantic_stack')
        if isinstance(stack.peek(), (StatList, Statement)):
            block_one = stack.pop()
            if isinstance(stack.peek(), (StatList, Statement)):
                kwargs['else'] = block_one
                kwargs['then'] = stack.pop()
            else:
                kwargs['then'] = block_one
        kwargs['rel_expr'] = stack.pop()
        return If(**kwargs)

    @staticmethod
    def create_while(**kwargs) -> AbstractSyntaxNode:
        stack: Stack = kwargs.get('semantic_stack')
        if isinstance(stack.peek(), (StatList, Statement)):
            kwargs['stat'] = stack.pop()
        kwargs['rel_expr'] = stack.pop()
        return While(**kwargs)

    @staticmethod
    def create_read(**kwargs) -> AbstractSyntaxNode:
        kwargs['var'] = kwargs.get('semantic_stack').pop()
        return Read(**kwargs)

    @staticmethod
    def create_list(list_name: str, elem_type: Union[Type, Tuple[Type, ...]], container_type: Type, **kwargs):
        stack: Stack = kwargs.get('semantic_stack')
        kwargs[list_name] = []
        while len(stack) > 0 and isinstance(stack.peek(), elem_type):
            kwargs[list_name].append(stack.pop())
        # inheritance list is greedy, will consume one extra ID
        if 'extra_func' in kwargs.keys():
            # return the id
            kwargs['extra_func'](**kwargs)
        kwargs[list_name] = kwargs[list_name][-1::-1]
        return container_type(**kwargs)

    @staticmethod
    def create_write(**kwargs) -> AbstractSyntaxNode:
        kwargs['expr'] = kwargs.get('semantic_stack').pop()
        return Write(**kwargs)

    @staticmethod
    def create_return(**kwargs) -> AbstractSyntaxNode:
        kwargs['expr'] = kwargs.get('semantic_stack').pop()
        return Return(**kwargs)

    @staticmethod
    def create_prog(**kwargs):
        stack: Stack = kwargs.get('semantic_stack')
        kwargs['main']: AbstractSyntaxNode = stack.pop()
        if not stack.is_empty():
            kwargs['funcs']: AbstractSyntaxNode = stack.pop()
        else:
            kwargs['funcs'] = None
        if not stack.is_empty():
            kwargs['classes']: AbstractSyntaxNode = stack.pop()
        else:
            kwargs['classes'] = None
        return ProgramNode(**kwargs)

    @staticmethod
    def create_class_list(**kwargs):
        return AbstractSyntaxNodeFactory.create_list('classes', ClassDecl, ClassList, **kwargs)

    @staticmethod
    def create_member_list(**kwargs):
        return AbstractSyntaxNodeFactory.create_list('members', (FuncDecl, VarDecl), MemberList, **kwargs)

    @staticmethod
    def create_func_list(**kwargs):
        return AbstractSyntaxNodeFactory.create_list('funcs', FuncDef, FuncDefList, **kwargs)

    @staticmethod
    def create_idx_list(**kwargs):
        return AbstractSyntaxNodeFactory.create_list('indices', (Expr, ), IndList, extra_func=AbstractSyntaxNodeFactory.sep_remover, **kwargs)

    @staticmethod
    def create_inherit_list(**kwargs):
        return AbstractSyntaxNodeFactory.create_list('inherit', Leaf, InheritList, extra_func=AbstractSyntaxNodeFactory.sep_remover, **kwargs)

    @staticmethod
    def create_class(**kwargs):
        stack: Stack = kwargs.get('semantic_stack')
        kwargs['members']: AbstractSyntaxNode = stack.pop()
        if len(stack) > 0 and isinstance(stack.peek(), InheritList):
            kwargs['inherit'] = stack.pop()
        kwargs['id']: AbstractSyntaxNode = stack.pop()
        return ClassDecl(**kwargs)

    @staticmethod
    def create_member_func(**kwargs):
        stack: Stack = kwargs.get('semantic_stack')
        kwargs['type']: AbstractSyntaxNode = stack.pop()
        kwargs['params']: AbstractSyntaxNode = stack.pop()
        kwargs['id']: AbstractSyntaxNode = stack.pop()
        if stack.peek() == 'VIS':
            stack.pop()
            kwargs['vis'] = stack.pop()
        if stack.peek() == 'SR':
            stack.pop()
            kwargs['class'] = stack.pop()
        return FuncDecl(**kwargs)

    @staticmethod
    def create_member_var(**kwargs):
        stack: Stack = kwargs.get('semantic_stack')
        kwargs['dims']: AbstractSyntaxNode = stack.pop()
        kwargs['id']: AbstractSyntaxNode = stack.pop()
        kwargs['type']: AbstractSyntaxNode = stack.pop()
        if stack.peek() == 'VIS':
            stack.pop()
            kwargs['vis'] = stack.pop()
        return VarDecl(**kwargs)

    @staticmethod
    def add_sep(**kwargs):
        return 'SEPARATOR'

    @staticmethod
    def add_vis(**kwargs):
        return 'VIS'

    @staticmethod
    def add_sr(**kwargs):
        return 'SR'


    @staticmethod
    def create_f_param(**kwargs):
        stack: Stack = kwargs.get('semantic_stack')
        kwargs['dims']: AbstractSyntaxNode = stack.pop()
        kwargs['id']: AbstractSyntaxNode = stack.pop()
        kwargs['type']: AbstractSyntaxNode = stack.pop()
        return FParam(**kwargs)

    @staticmethod
    def create_f_param_list(**kwargs):
        return AbstractSyntaxNodeFactory.create_list('params', FParam, FParamList, **kwargs)

    @staticmethod
    def sep_remover(**kwargs):
        # remove the separator
        if kwargs['semantic_stack'].peek() == 'SEPARATOR':
            kwargs['semantic_stack'].pop()

    @staticmethod
    def create_dim_list(**kwargs):
        return AbstractSyntaxNodeFactory.create_list('dims', Leaf, DimList, extra_func=AbstractSyntaxNodeFactory.sep_remover, **kwargs)

    @staticmethod
    def create_a_param_list(**kwargs):
        return AbstractSyntaxNodeFactory.create_list('params', Expr, AParamList, extra_func=AbstractSyntaxNodeFactory.sep_remover, **kwargs)

    @staticmethod
    def create_var_list(**kwargs):
        return AbstractSyntaxNodeFactory.create_list('vars', VarDecl, VarDeclList, **kwargs)

    @staticmethod
    def create_statement_list(**kwargs):
        return AbstractSyntaxNodeFactory.create_list('stats', Statement, StatList, **kwargs)

    @staticmethod
    def create_statement(**kwargs) -> AbstractSyntaxNode:
        kwargs['stat'] = kwargs.get('semantic_stack').pop()
        return Statement(**kwargs)

    @staticmethod
    def create_func_body(**kwargs) -> AbstractSyntaxNode:
        stack: Stack = kwargs.get('semantic_stack')
        kwargs['stats'] = stack.pop()
        if isinstance(stack.peek(), VarDeclList):
            kwargs['vars'] = stack.pop()
        return FuncBody(**kwargs)

    @staticmethod
    def create_var(**kwargs):
        """

        GLOB IS ANYTHING TO THE LEFT OF AN ASSIGNMENT OPERATOR
        EX - WHATS IN PARENTHESES:
        (test.thats[6][16+8]) = 5
        """
        return AbstractSyntaxNodeFactory.create_list('components', (Leaf, IndList, AParamList), Var, **kwargs)

    @staticmethod
    def create_func(**kwargs):
        stack: Stack = kwargs.get('semantic_stack')
        kwargs['body'] = stack.pop()
        kwargs['head'] = stack.pop()
        return FuncDef(**kwargs)

    @staticmethod
    def make_tern(**kwargs):
        stack: Stack = kwargs.get('semantic_stack')
        kwargs['false'] = stack.pop()
        kwargs['true'] = stack.pop()
        kwargs['condition'] = stack.pop()
        return Ternary(**kwargs)
