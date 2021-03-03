from pycompile.parser.syntax.ast import AbstractSyntaxNode


class ProgramNode(AbstractSyntaxNode):
    NUM_NODES = 3


class ClassList(AbstractSyntaxNode):
    pass


class FuncDefList(AbstractSyntaxNode):
    pass


class ClassDecl(AbstractSyntaxNode):
    NUM_NODES = 3


class FuncDef(AbstractSyntaxNode):
    NUM_NODES = 5


class InheritList(AbstractSyntaxNode):
    NUM_NODES = -1


class MemberList(AbstractSyntaxNode):
    NUM_NODES = -1


class Visibility(AbstractSyntaxNode):
    NUM_NODES = 1


class MemberDecl(AbstractSyntaxNode):
    NUM_NODES = (1, 3)


class FParam(AbstractSyntaxNode):
    NUM_NODES = 3


class DimList(AbstractSyntaxNode):
    ...


class FParamList(AbstractSyntaxNode):
    ...

