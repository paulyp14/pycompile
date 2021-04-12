from __future__ import annotations
from enum import Enum
from typing import List, Optional, Union, Dict
from pycompile.parser.syntax.node import VarDecl, ClassDecl, FuncDecl, FParam, AbstractSyntaxNode
from pycompile.symbol.error import InheritanceError


class Visibility(Enum):
    Private = 1
    Public = 2

    @staticmethod
    def get_visibility(leaf) -> Visibility:
        trans = {
            None: Visibility.Public,
            'public': Visibility.Public,
            'private': Visibility.Private
        }
        return trans[None if leaf is None else leaf.token.lexeme]


class Kind(Enum):
    Function = 1
    Variable = 2
    Class = 3
    Parameter = 4
    InheritanceRelation = 5

    @staticmethod
    def get_kind(node: AbstractSyntaxNode) -> Kind:
        trans = {
            VarDecl: Kind.Variable,
            FuncDecl: Kind.Function,
            ClassDecl: Kind.Class,
            FParam: Kind.Parameter
        }
        return trans[type(node)]

    def __str__(self):
        return self.name


class TypeEnum(Enum):
    Integer = 1
    Float = 2
    String = 3
    Class = 4
    Void = 5

    @staticmethod
    def match(one: TypeEnum, two: TypeEnum) -> bool:
        return (
            (one in (TypeEnum.Float, TypeEnum.Integer) and two in (TypeEnum.Float, TypeEnum.Integer)) or
            one == two
        )

    @staticmethod
    def is_class(name: str) -> bool:
        return name not in ('integer', 'float', 'string', 'void', 'main')


class Type:
    def __init__(self, enum: TypeEnum, type_name: str):
        self.enum = enum
        self.type_name = type_name

    @staticmethod
    def get_type(node: Union[VarDecl, FuncDecl, FParam]) -> Type:
        trans = {
            'float': TypeEnum.Float,
            'integer': TypeEnum.Integer,
            'string': TypeEnum.String,
            'void': TypeEnum.Void
        }
        type_val = trans.get(node.type.token.lexeme, TypeEnum.Class)
        name = node.type.token.lexeme
        return Type(type_val, name)

    @staticmethod
    def get_type_from_token(node) -> Type:
        trans = {
            'Float': TypeEnum.Float,
            'Integer': TypeEnum.Integer,
            'String': TypeEnum.String,
        }
        token_name = node.child.token.__class__.__name__
        type_val = trans.get(token_name, TypeEnum.Class)
        if type_val == TypeEnum.Class:
            name = node.type.token.lexeme
            pass
        else:
            name = type_val.name.lower()
        return Type(type_val, name)

    def __str__(self):
        return self.type_name

    def __eq__(self, other):
        if not isinstance(other, Type):
            return False
        return self.enum == other.enum and (self.enum != TypeEnum.Class or self.type_name == other.type_name)


class SemanticRecord:
    RECORD_LIST: List[SemanticRecord] = []

    def __init__(self,
                 record_name: str,
                 record_kind: Kind,
                 record_type: Type = None,
                 is_array: bool = False,
                 dimensions: int = 0,
                 dimension_list: Dict[int, int] = None,
                 member_of: str = None,
                 inheritances: List[str] = None,
                 visibility: Visibility = None
                 ):
        self.name: str = record_name
        self.kind: Kind = record_kind
        self.type: Type = record_type
        self.is_array: bool = is_array
        self.dimensions: int = dimensions
        self.dimension_dict: Dict[int, int] = dimension_list
        """ :type pycompile.symbol.stable.SymbolTable """
        self.table_link = None
        self.member_of: Optional[str] = member_of
        self.inheritances: Optional[List[str]] = inheritances
        self.visibility: Optional[Visibility] = visibility
        self.parent_tables: List = []
        self.position: Optional[int] = None
        self.memory_size: int = 0
        self.mem_offset: Optional[int] = None
        self.from_var: bool = False

        self.RECORD_LIST.append(self)

    def set_link(self, symbol_table):
        self.table_link = symbol_table

    def get_name(self):
        memb_name = f'{self.member_of}::' if self.member_of is not None and self.kind == Kind.Function else ''
        return f"{memb_name}{self.name}"

    def func_equality(self, other: SemanticRecord) -> bool:
        # allow function overloading
        # to allow it, have to make sure that function params are different
        # difference can be in number of params, or type of params
        func_eq = True
        self_params = [fp for fp in self.table_link.records.values() if fp.kind == Kind.Parameter]
        other_params = [fp for fp in other.table_link.records.values() if fp.kind == Kind.Parameter]
        if len(other_params) == len(self_params):
            func_eq = all([sfp.f_param_eq(ofp) for sfp, ofp in zip(self_params, other_params)])
        else:
            func_eq = False
        return func_eq

    def __eq__(self, other) -> bool:
        if not isinstance(other, SemanticRecord):
            return False
        if self.kind == Kind.Function and other.kind == Kind.Function:
            func_eq = self.func_equality(other)
        else:
            func_eq = True
        return (
                self.get_name() == other.get_name() and
                self.type == other.type and
                self.kind == other.kind and
                self.is_array == other.is_array and
                self.dimensions == other.dimensions and
                self.dimension_dict == other.dimension_dict and
                self.member_of == other.member_of and
                func_eq
        )

    def f_param_eq(self, other: SemanticRecord) -> bool:
        return (
                self.type == other.type and
                self.is_array == other.is_array and
                self.dimensions == other.dimensions and
                self.dimension_dict == other.dimension_dict
        )

    def f_param_repr(self) -> str:
        as_str = str(self.type)
        if self.dimensions > 0:
            for idx in range(self.dimensions):
                if self.dimension_dict is not None:
                    as_str += f'[{self.dimension_dict[idx] if self.dimension_dict[idx] is not None else ""}]'
                else:
                    as_str += '[]'
        return as_str

    def get_func_decl(self) -> str:
        if self.table_link is None:
            params = ''
        else:
            params = ', '.join(
                [fp.f_param_repr() for fp in self.table_link.records.values() if fp.kind == Kind.Parameter])
            params = f'({params})'
        return f'{self.get_name()}{params}'

    def investigate_inheritance(self, global_table, subclass_list, tree_set) -> bool:
        if self.name in subclass_list:
            return False
        inherit_list = self.inheritances if self.inheritances is not None else []
        if len(inherit_list) == 0:
            full_tree = subclass_list + [self.name]
            tree_set.add('-'.join(full_tree[-1::-1]))
            return True
        else:
            res = []
            for class_name in inherit_list:
                class_def = global_table.records.get(class_name)
                if class_def is None:
                    raise InheritanceError(class_name)
                res.append(class_def.investigate_inheritance(global_table, subclass_list + [self.name], tree_set))
            return all(res)

    @staticmethod
    def verify_all_classes_exist(global_table):
        pass

    def array_repr(self, min_len: int = 0) -> List[str]:
        if self.kind == Kind.Class:
            as_str = f' class     | {self.name} '
            return [f'{as_str}{(min_len - len(as_str)) * " "}']
        elif self.kind == Kind.Variable:
            data_type_name = 'data' if self.member_of is not None else 'local'
            access_modifier = self.visibility.name.lower() if self.visibility is not None else ''
            vis = f' | {access_modifier}' if access_modifier != '' else ''
            as_str = f' {data_type_name} | {self.name} | {self.f_param_repr()}{vis}'
            return [f'{as_str}{(min_len - len(as_str)) * " "}']
        elif self.kind == Kind.Function:
            as_str = f' function    | {self.name} '
            if self.name != 'main':
                self_params = [fp.f_param_repr() for fp in self.table_link.records.values() if fp.kind == Kind.Parameter]
                if len(self_params) > 0:
                    f_repr = f' | ({", ".join(self_params)})'
                else:
                    f_repr = "| ()"
                f_repr += f" : {self.type.type_name if self.type is not None else 'SemErr'}"
            else:
                f_repr = ''
            access_modifier = self.visibility.name.lower() if self.visibility is not None else ''
            vis = f' | {access_modifier}' if access_modifier != '' else ''
            as_str = f'{as_str}{f_repr}{vis}'
            return [f'{as_str}{(min_len - len(as_str)) * " "}']
        elif self.kind == Kind.Parameter:
            as_str = f' param    | {self.name} | {self.f_param_repr()} '
            return [f'{as_str}{(min_len - len(as_str)) * " "}']
        elif self.kind == Kind.InheritanceRelation:
            print('Here')
        else:
            return [min_len * ' ']

    def get_length(self) -> int:
        return len(self.array_repr()[0])


class TypeRecord:

    def __init__(self, type: Type, is_array: bool = False, dimensions: int = 0, value: str = None):
        self.type = type
        # TODO translate the value
        self.is_array: bool = is_array
        self.dimensions: int = dimensions
        self.value = value
        self.position: Optional[int] = None

    def __str__(self):
        as_str = str(self.type)
        if self.dimensions is not None:
            for i in range(self.dimensions):
                as_str += '[]'
        return as_str