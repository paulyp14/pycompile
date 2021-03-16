from pycompile.lex.token import *
from pycompile.parser.syntax.ast import AbstractSyntaxNode


class ProgramNode(AbstractSyntaxNode):
    NUM_NODES = 3

    CHILDREN = ['class_list', 'func_list', 'main']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # if not isinstance(kwargs['classes'], ClassList) or not isinstance(kwargs['funcs'], FuncDefList) or not isinstance(kwargs['main'], FuncBody):
        #     raise RuntimeError()
        self.class_list: AbstractSyntaxNode = kwargs.get('classes')
        self.func_list: AbstractSyntaxNode = kwargs.get('funcs')
        self.main: AbstractSyntaxNode = kwargs.get('main')


class ClassList(AbstractSyntaxNode):
    NUM_NODES = -1

    CHILDREN = ['classes']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if len(kwargs['classes']) > 0 and not isinstance(kwargs['classes'][0], ClassDecl):
            raise RuntimeError()
        self.classes = kwargs.get('classes', [])


class FuncDefList(AbstractSyntaxNode):
    NUM_NODES = -1

    CHILDREN = ['funcs']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if len(kwargs['funcs']) > 0 and (not isinstance(kwargs['funcs'][0], FuncDef) and not isinstance(kwargs['funcs'][0], FuncDecl)):
            raise RuntimeError()
        self.funcs = kwargs.get('funcs', [])


class ClassDecl(AbstractSyntaxNode):
    NUM_NODES = 3

    CHILDREN = ['id', 'inherit_list', 'member_list']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.id = kwargs.get('id')
        self.inherit_list = kwargs.get('inherit')
        self.member_list = kwargs.get('members')


class FuncDef(AbstractSyntaxNode):
    NUM_NODES = 2

    CHILDREN = ['head', 'body']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.head = kwargs.get('head')
        self.body = kwargs.get('body')


class InheritList(AbstractSyntaxNode):
    NUM_NODES = -1

    CHILDREN = ['parents']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.parents = kwargs.get('inherit', [])


class MemberList(AbstractSyntaxNode):
    NUM_NODES = -1

    CHILDREN = ['members']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.members = kwargs.get('members', [])


class MemberDecl(AbstractSyntaxNode):
    NUM_NODES = 1


class FParam(AbstractSyntaxNode):

    CHILDREN = ['type', 'id', 'dim_list']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.id = kwargs.get('id')
        self.type = kwargs.get('type')
        self.dim_list = kwargs.get('dims')


class DimList(AbstractSyntaxNode):
    NUM_NODES = -1

    CHILDREN = ['dims']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dims = kwargs.get('dims', [])


class FParamList(AbstractSyntaxNode):
    NUM_NODES = -1

    CHILDREN = ['params']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.params = kwargs.get('params', [])


class AParamList(AbstractSyntaxNode):
    NUM_NODES = -1

    CHILDREN = ['params']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.params = kwargs.get('params', [])


class VarDeclList(AbstractSyntaxNode):
    NUM_NODES = -1

    CHILDREN = ['vars']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.vars = kwargs.get('vars', [])


class StatList(AbstractSyntaxNode):
    NUM_NODES = -1

    CHILDREN = ['stats']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stats = kwargs.get('stats', [])


class Statement(AbstractSyntaxNode):
    NUM_NODES = -1

    CHILDREN = ['statement']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statement = kwargs.get('stat')


class Leaf(AbstractSyntaxNode):
    NUM_NODES = 0

    CHILDREN = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.token: Token = kwargs.get('token')


class Operator(AbstractSyntaxNode):
    NUM_NODES = 2

    CHILDREN = ['left_operand', 'right_operand']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.left_operand: AbstractSyntaxNode = kwargs.get('left_operand')
        self.operator: str = kwargs.get('operator')
        self.right_operand: AbstractSyntaxNode = kwargs.get('right_operand')


class Term(AbstractSyntaxNode):
    NUM_NODES = 1

    CHILDREN = ['factor']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.factor: AbstractSyntaxNode = kwargs.get('factor')


class Factor(AbstractSyntaxNode):
    NUM_NODES = 1

    CHILDREN = ['child']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.child: AbstractSyntaxNode = kwargs.get('child')


class Expr(AbstractSyntaxNode):
    NUM_NODES = 1

    CHILDREN = ['arith_expr']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.arith_expr: AbstractSyntaxNode = kwargs.get('arith_expr')


class ArithExpr(AbstractSyntaxNode):
    NUM_NODES = 1

    CHILDREN = ['arith_expr']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.arith_expr: AbstractSyntaxNode = kwargs.get('term')


class Negation(AbstractSyntaxNode):
    NUM_NODES = 2

    CHILDREN = ['op', 'factor']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.factor: AbstractSyntaxNode = kwargs.get('factor')
        self.op: str = kwargs.get('op')


class Signed(AbstractSyntaxNode):
    NUM_NODES = 2

    CHILDREN = ['op', 'factor']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.factor: AbstractSyntaxNode = kwargs.get('factor')
        self.op: str = kwargs.get('op')


class Continue(Leaf):
    ...


class Break(Leaf):
    ...


class If(AbstractSyntaxNode):
    NUM_NODES = 3

    CHILDREN = ['rel_expr', 'then_block', 'else_block']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rel_expr: AbstractSyntaxNode = kwargs.get('rel_expr')
        self.then_block: AbstractSyntaxNode = kwargs.get('then')
        self.else_block: AbstractSyntaxNode = kwargs.get('else')


class While(AbstractSyntaxNode):
    NUM_NODES = 2

    CHILDREN = ['rel_expr', 'stat_block']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rel_expr: AbstractSyntaxNode = kwargs.get('rel_expr')
        self.stat_block: AbstractSyntaxNode = kwargs.get('stat')


class Read(AbstractSyntaxNode):
    NUM_NODES = 1

    CHILDREN = ['var']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.var: AbstractSyntaxNode = kwargs.get('var')


class Write(AbstractSyntaxNode):
    NUM_NODES = 1

    CHILDREN = ['expr']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.expr: AbstractSyntaxNode = kwargs.get('expr')


class Return(AbstractSyntaxNode):
    NUM_NODES = 1

    CHILDREN = ['expr']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.expr: AbstractSyntaxNode = kwargs.get('expr')


class IndList(AbstractSyntaxNode):
    NUM_NODES = -1

    CHILDREN = ['indices']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.indices = kwargs.get('indices', [])


class FuncDecl(AbstractSyntaxNode):
    NUM_NODES = 3

    CHILDREN = ['visibility', 'id', 'my_class', 'fparam_list', 'type']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.id = kwargs.get('id')
        self.type = kwargs.get('type')
        self.fparam_list = kwargs.get('params')
        self.visibility = kwargs.get('vis')
        self.my_class = kwargs.get('class')


class VarDecl(AbstractSyntaxNode):
    NUM_NODES = 3

    CHILDREN = ['visibility', 'type', 'id', 'dim_list']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.id = kwargs.get('id')
        self.type = kwargs.get('type')
        self.dim_list = kwargs.get('dims')
        self.visibility = kwargs.get('vis')


class FuncBody(AbstractSyntaxNode):
    NUM_NODES = 2

    CHILDREN = ['vars', 'stats']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.vars = kwargs.get('vars')
        self.stats = kwargs.get('stats')


class Var(AbstractSyntaxNode):
    NUM_NODES = -1

    CHILDREN = ['components']

    """
        
    GLOB IS ANYTHING TO THE LEFT OF AN ASSIGNMENT OPERATOR
    EX - WHATS IN PARENTHESES:
    (test.thats[6][16+8]) = 5 
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.components = kwargs.get('components')


class Ternary(AbstractSyntaxNode):
    NUM_NODES = 3

    CHILDREN = ['condition', 'true_expr', 'false_expr']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.condition = kwargs.get('condition')
        self.true_expr = kwargs.get('true')
        self.false_expr = kwargs.get('false')
