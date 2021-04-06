from typing import List, Optional, Union

from pycompile.parser.syntax.node import *
from pycompile.symbol.stable import SymbolTable
from pycompile.symbol.error import SemanticError, SemanticWarning, InheritanceError
from pycompile.symbol.record import SemanticRecord, Kind, Type, TypeEnum, TypeRecord, Visibility


class Visitor:
    def __init__(self):
        self.global_table: Optional[SymbolTable] = None
        self.errors: List[Union[SemanticError, SemanticWarning]] = []

    def visit(self, node: AbstractSyntaxNode):
        pass

    def finish(self):
        pass

    def pre_visit(self, node: AbstractSyntaxNode):
        pass


class SemanticTableBuilder(Visitor):

    def __init__(self):
        super().__init__()
        self.inheritance_trees = set()

    def visit(self, node: AbstractSyntaxNode):
        if isinstance(node, ProgramNode):
            pass

        if isinstance(node, (VarDecl, ClassDecl, FuncDecl, FParam)):
            # create semantic records
            kind = Kind.get_kind(node)
            n_type = None
            name = node.id.token.lexeme
            member_of, vis = None, None
            inheritances = None
            if isinstance(node, (VarDecl, FuncDecl, FParam)):
                n_type = Type.get_type(node)
                if n_type.enum == TypeEnum.Class:
                    # search, make sure class exists
                    # DOING THIS ELSEWHERE
                    pass
            if isinstance(node, VarDecl):
                # check for dimensions
                if isinstance(node.parent, MemberList):
                    # add member of for declarations inside class decls
                    member_of = node.parent.parent.id.token.lexeme
                    vis = Visibility.get_visibility(node.visibility)
            if isinstance(node, FuncDecl):
                if isinstance(node.parent, MemberList):
                    # add member of for declarations inside class decls
                    member_of = node.parent.parent.id.token.lexeme
                    vis = Visibility.get_visibility(node.visibility)
                elif isinstance(node.parent, FuncDef) and node.my_class is not None:
                    # add member of for implementations
                    member_of = node.my_class.token.lexeme
            if isinstance(node, ClassDecl) and node.inherit_list is not None:
                # add inherited classes so that symbol tables can be merged
                inheritances = []
                for child in node.inherit_list.get_children():
                    inheritances.append(child.token.lexeme)
            rec = SemanticRecord(name, kind, n_type, member_of=member_of, inheritances=inheritances, visibility=vis)
            node.sem_rec = rec

            # add position information for these guys so errors can be more helpful
            node.sem_rec.position = node.id.token.position

            if isinstance(node, (VarDecl, FParam)):
                # CHECK DIMENSIONS
                if len(node.dim_list.get_children()) > 0:
                    # its an array, set dimensions
                    rec.is_array = True
                    rec.dimensions = len(node.dim_list.get_children())
                    for idx, dim in enumerate(node.dim_list.get_children()):
                        # if size of dimensions specified, set them
                        if not isinstance(dim.token, Placeholder):
                            if rec.dimension_dict is None:
                                rec.dimension_dict = {}
                            rec.dimension_dict[idx] = int(dim.token.lexeme)

        if isinstance(node, (FuncBody, ClassDecl, FuncDecl, ProgramNode)):
            # create symbol tables
            if (isinstance(node, FuncBody) and isinstance(node.parent, ProgramNode)) or isinstance(node, (FuncDecl, ClassDecl)):
                if isinstance(node, FuncBody):
                    name = 'main'
                    rec = SemanticRecord(name, Kind.Function)
                    node.sem_rec = rec
                else:
                    name = rec.get_name()
                sym_table = SymbolTable(name)
                node.sym_table = sym_table
                rec.set_link(sym_table)
            elif isinstance(node, ProgramNode):
                # do program node
                self.global_table = SymbolTable('global')
                node.sym_table = self.global_table
                sym_table = self.global_table
            else:
                rec = node.parent.head.sem_rec
                name = rec.get_name()
                sym_table = rec.table_link

            # need to populate symbol tables
            children = []
            if isinstance(node, FuncBody) and isinstance(node.vars, VarDeclList):
                children = node.vars.get_children()
            elif isinstance(node, ClassDecl):
                children = node.member_list.get_children()
            elif isinstance(node, FuncDecl):
                children = node.fparam_list.get_children()
            elif isinstance(node, ProgramNode):
                # add all classes, funcs, and main func to global_table
                children += node.class_list.get_children() if node.class_list is not None else []
                children += [child.head for child in node.func_list.get_children()]
                children += [node.main]

            for child in children:
                crec = child.sem_rec
                if sym_table.already_defined(crec):
                    msg = 'Multiply declared {}{}'
                    in_msg = ': {} in {}'
                    pos_msg = f'(line: {crec.position})'
                    in_msg = f'{in_msg} {pos_msg}'
                    if crec.kind == Kind.Variable:
                        if crec.member_of is None:
                            kind = 'local variable'
                            parent = sym_table.name
                        else:
                            kind = 'data member'
                            parent = crec.member_of
                        msg = msg.format(kind, in_msg.format(crec.get_name(), parent))
                    elif crec.kind == Kind.Function:
                        # function equality has already been checked in already_defined
                        if crec.member_of is None:
                            kind = 'free function'
                            in_msg = f': {crec.get_func_decl()} {pos_msg}'
                        else:
                            kind = 'member function'
                            in_msg = in_msg.format(crec.get_func_decl(), crec.member_of)
                        msg = msg.format(kind, in_msg)
                    elif crec.kind == Kind.Parameter:
                        sym_table.add_record(crec, sym_table.generate_duplicated_param_name(crec))
                        msg = msg.format('function parameter', f': {crec.get_name()} in {rec.get_func_decl()} {pos_msg}')
                    else:
                        msg = msg.format('class', f': {crec.get_name()} {pos_msg}')
                    self.errors.append(SemanticError(msg))
                else:
                    if sym_table.overloaded(crec):
                        if not isinstance(node, ProgramNode) or (isinstance(node, ProgramNode) and crec.member_of is None):
                            # prevent duplicate warnings for implmenetations of member functions
                            pos_msg = f'(line: {crec.position})'
                            self.errors.append(SemanticWarning(
                                f'The function {sym_table.get_overloaded(crec)} has been overloaded by {crec.get_func_decl()} {pos_msg}'
                            ))
                        sym_table.add_overloaded_record(crec)
                    else:
                        sym_table.add_record(crec)

    def finish(self):
        # merge class function implementations with declarations
        for rec in self.global_table.records.values():
            rec_pos_msg = f'(line: {rec.position})'
            if rec.kind == Kind.Class:
                for class_rec in rec.table_link.records.values():
                    pos_msg = f'(line: {class_rec.position})'
                    other_names = [r.name for r in rec.table_link.records.values() if r.kind != class_rec.kind]
                    if class_rec.name in other_names:
                        other_kind = 'Variable' if class_rec.kind == Kind.Function else 'Function'
                        self.errors.append(SemanticError(f'In {rec.table_link.name}, {class_rec.kind.name} with name "{class_rec.name}" clashes with {other_kind} of same name'))
                    if class_rec.kind == Kind.Function:
                        """
                        Guarantee Fparams and merge implementations and decls of member funcs
                        """
                        errors = False
                        cf_name = self.global_table.get_overloaded_name(class_rec)
                        body_def = self.global_table.records.get(cf_name)
                        if body_def is None:
                            errors = True
                            self.errors.append(SemanticError(f'No definition for declared member function: {cf_name} {pos_msg}'))
                            continue

                        if len(body_def.table_link.records.keys()) < len(class_rec.table_link.records.keys()):
                            errors = True
                            self.errors.append(SemanticError(
                                f'Too few function parameters: function declared as {class_rec.get_func_decl()} implemented as {body_def.get_func_decl()} {pos_msg}'
                            ))
                        fpr = [r for r in class_rec.table_link.records.values() if r.kind == Kind.Parameter]
                        fpm = [r for r in body_def.table_link.records.values() if r.kind == Kind.Parameter]
                        for fp_rec, matching_rec in zip(fpr, fpm):
                            if fp_rec != matching_rec:
                                errors = True
                                self.errors.append(SemanticError(
                                    f'Declaration of member function {cf_name} does not match implementation: parameters {fp_rec.name} and {matching_rec.name} differ {pos_msg}'
                                ))
                        if not errors:
                            # get rid of the partial link in the class decl, and replace it with full table in
                            class_rec.table_link = body_def.table_link
                            class_rec.table_link.matched = True
                if not TypeEnum.is_class(class_rec.type.type_name) or class_rec.type.type_name in self.global_table.records.keys():
                    continue
                # the type of the variable / param is an undeclared class
                self.errors.append(
                    SemanticError(f'The variable {class_rec.get_name()} is of undefined type {class_rec.type.type_name} {pos_msg}')
                )
                """
                Merge inherited classes
                """
                for class_name in (rec.inheritances if rec.inheritances is not None else []):
                    parent = self.global_table.records.get(class_name)
                    if parent is None:
                        self.errors.append(SemanticError(f'Declared parent class {class_name} of {rec.get_name()} does not exist {rec_pos_msg}'))
                        break
                    parent_table = parent.table_link
                    rec.parent_tables.append(parent_table)
            elif rec.kind == Kind.Function:
                if rec.member_of is not None and not rec.table_link.matched:
                    self.errors.append(SemanticError(f'Definition provided for undeclared member function: {rec.get_func_decl()} {rec_pos_msg}'))
                for frec in rec.table_link.records.values():
                    frec_pos = f'(line: {frec.position})'
                    if not TypeEnum.is_class(frec.type.type_name) or frec.type.type_name in self.global_table.records.keys():
                        continue
                    # the type of the variable / param is an undeclared class
                    self.errors.append(
                        SemanticError(f'The variable {frec.name} is of undefined type {frec.type.type_name} {frec_pos}')
                    )
        """
        PASS 2

        FINDING CIRCULAR DEPENDENCIES
        """
        class_list = [rec.name for rec in self.global_table.records.values() if rec.kind == Kind.Class]
        for class_name in class_list:
            rec = self.global_table.records.get(class_name)
            pos_msg = f'(line: {rec.position})'
            # check for cyclic dependencies in parent-child class relationships
            try:
                valid_scheme = rec.investigate_inheritance(self.global_table, [], self.inheritance_trees)
                if not valid_scheme:
                    self.errors.append(SemanticError(
                        f'Invalid inheritance scheme found for {class_name} (cyclic inheritance) {pos_msg}'
                    ))
            except InheritanceError as e:
                self.errors.append(SemanticError(f'Invalid inheritance scheme found for {class_name} - inheriting from undeclared class {e.inherit_name} {pos_msg}'))
        """
        PASS 3
        
        FINDING SHADOWED VARS
        """
        for rec in self.global_table.records.values():
            # do it for
            # warn about shadowed variables
            if rec.table_link is not None and rec.kind == Kind.Function and rec.member_of is None:
                # do it only for functions for now, which have one level
                global_as_outer = SymbolTable('outer')
                for inner_rec in self.global_table.records.values():
                    if inner_rec.kind != Kind.Function or inner_rec.member_of is None:
                        global_as_outer.add_record(inner_rec)
                rec.table_link.find_shadowed_vars(global_as_outer, self.errors)
        inherit_checks = {
            k: {'list': [], 'done': False} for k in class_list
        }
        sorted_trees = sorted(self.inheritance_trees, key=lambda x: len(x))
        for tree in sorted_trees:
            classes = tree.split('-')
            fake_class_tables = []
            # create copies of each classes' symbol table
            for class_ in classes:
                real_table = self.global_table.records.get(class_)
                if real_table is None:
                    # stop processing the second a hierarchy becomes invalid
                    break
                fake_table = SymbolTable(class_)
                for key, rec in real_table.table_link.records.items():
                    fake_table.records[key] = rec
                fake_class_tables.append(fake_table)
            # create records to link classes, from base to most derived child
            for idx, class_ in enumerate(classes):
                if idx == 0:
                    continue
                parent_table = fake_class_tables[idx - 1]
                child_table = fake_class_tables[idx]
                fake_rec = SemanticRecord(f'RelRec{idx}', Kind.InheritanceRelation)
                parent_table.add_record(fake_rec)
                fake_rec.set_link(child_table)
            # create a symbol table with global symbols
            global_as_outer = SymbolTable('outer')
            for inner_rec in self.global_table.records.values():
                if inner_rec.kind != Kind.Function or inner_rec.member_of is None:
                    global_as_outer.add_record(inner_rec)
            # start at biggest ancestor, whose outer scope is the copy of global
            fake_class_tables[0].find_shadowed_vars(
                global_as_outer,
                self.errors,
                for_classes=True,
                global_table=self.global_table,
                inherit_checks=inherit_checks
            )
            if not inherit_checks[fake_class_tables[0].name]['done']:
                inherit_checks[fake_class_tables[0].name]['done'] = True


class TypeChecker(Visitor):
    def __init__(self, table: SymbolTable, errors: List[Union[SemanticWarning, SemanticError]]):
        super().__init__()
        self.ignored_nodes: set = set()
        self.skip: bool = True
        self.current_scope: List[str] = []
        self.global_table: SymbolTable = table
        if isinstance(errors, list):
            self.errors: List[Union[SemanticWarning, SemanticError]] = errors
        else:
            self.errors = []
        self.return_types = []

    def pre_visit(self, node: AbstractSyntaxNode):
        if isinstance(node, FuncDef):
            node.sym_table = node.head.sym_table
            node.sem_rec = node.head.sem_rec
            node.head.sym_table = None
            node.head.sem_rec = None
        if node.sym_table is not None:
            if node.sem_rec is None:
                self.current_scope.append(node.sym_table.name)
            else:
                if self.global_table.was_overloaded(node.sem_rec):
                    scope_name = node.sem_rec.get_func_decl()
                else:
                    scope_name = node.sem_rec.get_name()
                self.current_scope.append(scope_name)
        if isinstance(node, FuncBody):
            self.skip = False
            self.return_types = []

    def visit(self, node: AbstractSyntaxNode):
        if self.skip:
            if node.sym_table is not None:
                self.current_scope = self.current_scope[:-1]
            return

        if isinstance(node, Factor) and isinstance(node.child, (Var, Leaf)):
            # can be leaf or Var or Signed or Not
            if isinstance(node.child, Leaf):
                # get the type from the token
                node.type_rec = TypeRecord(Type.get_type_from_token(node), value=node.child.token.lexeme)
                node.type_rec.position = node.child.token.position
            else:
                node.type_rec = node.child.type_rec

        elif isinstance(node, (ArithExpr, Expr, Term, Signed, Negation, Factor)):
            if isinstance(node, (ArithExpr, Expr)):
                node.type_rec = node.arith_expr.type_rec
            elif isinstance(node, (Term, Signed, Negation)):
                node.type_rec = node.factor.type_rec
            elif isinstance(node, Factor):
                node.type_rec = node.child.type_rec

        elif isinstance(node, Statement) and isinstance(node.statement, Var):
            node.type_rec = node.statement.type_rec
        elif isinstance(node, Statement):
            # and isinstance(node.statement, Operator):
            node.type_rec = node.statement.type_rec
            if isinstance(node.statement, Return):
                self.return_types.append(node.type_rec)
        # elif isinstance(node, Statement):
        #     print(f'Need to handle other types of Statement children: {node.statement.__class__.__name__}')
        elif isinstance(node, Operator):
            left_type = node.left_operand.type_rec
            right_type = node.right_operand.type_rec
            # TODO ALLOW NUMERIC MISMATCH.....
            if right_type is None or left_type is None:
                self.errors.append(SemanticError(
                    f'Failed to type operator {node.operator} because of semantic errors'
                ))
            elif not TypeEnum.match(left_type.type.enum, right_type.type.enum):
                pos_msg = f'(line: {left_type.position})'
                self.errors.append(SemanticError(
                    'Type mismatch: no operator {} exists between types {} and {} {}'.format(
                        node.operator,
                        left_type.type.type_name,
                        right_type.type.type_name,
                        pos_msg
                    )
                ))
            node.type_rec = left_type

        elif isinstance(node, Return):
            node.type_rec = node.expr.type_rec

        elif isinstance(node, Var):
            self.type_complex_statement(node)

        elif not isinstance(node, (VarDeclList, VarDecl, Var, AParamList, FuncBody, StatList, IndList, DimList, Leaf)):
            self.ignored_nodes.add(node.__class__.__name__)

        if node.sym_table is not None:
            self.current_scope = self.current_scope[:-1]

        if isinstance(node, FuncDef):
            func_rt = node.sem_rec.type
            node.type_rec = func_rt
            semantic_message = False
            if func_rt.enum == TypeEnum.Void and len(self.return_types) > 0:
                validated = False
            elif func_rt.enum == TypeEnum.Void and len(self.return_types) == 0:
                validated = True
            elif func_rt.enum != TypeEnum.Void and len(self.return_types) == 0:
                validated = False
            else:
                try:
                    validated = all([
                        TypeEnum.match(func_rt.enum, found_rt.type.enum)
                        for found_rt in self.return_types
                    ])
                except AttributeError as e:
                    semantic_message = True
            if semantic_message:
                msg = 'Type(s) of return statement(s) for function {} could not be validated because of semantic errors {}'
                self.errors.append(SemanticError(msg.format(node.sem_rec.get_func_decl(), f'(line: {node.sem_rec.position})')))
            elif not validated:
                self.errors.append(SemanticError(
                    'Type(s) of return statement(s) for function {} do no match with declared return type {} {}'.format(
                        node.sem_rec.get_func_decl(),
                        node.sem_rec.type.type_name,
                        f'(line: {node.sem_rec.position})'
                    )
                ))
            # reset
            self.return_types = []
            self.skip = True

    def get_scope(self, name: str = None):
        name = name if name is not None else self.current_scope[-1]
        scope_rec = self.global_table.records.get(name) if name != 'global' else None
        if name == 'global':
            scope_table = self.global_table
        else:
            rec = self.global_table.records.get(name)
            scope_table = rec.table_link if rec is not None else None
        return name, scope_rec, scope_table

    def type_complex_statement(self, node: AbstractSyntaxNode):
        sname, scope_rec, scope_table = self.get_scope()
        if scope_table is None:
            self.errors.append(SemanticError(f'FATAL: Can not resolve scope: {sname}'))
            return
        # isinstance(node.child, Var):
        comps = node.get_children()
        types = []
        for idx, base in enumerate(comps[::2]):
            list_idx = (idx * 2) + 1

            # TODO: check for void
            # if idx > 0 and the last type was VOID, then need an error

            # have to look in scopes
            name = base.token.lexeme
            # name represents a variable if the list accompanying it is an index list,
            # else it represents a function_call
            is_var = True if isinstance(comps[list_idx], IndList) else False
            if is_var:
                # if it's a variable, need to look up the variable, get its type
                # validate indexes list
                # look up
                error = None
                record = None
                if idx == 0 and name in scope_table.records.keys():
                    # it's a local var
                    record = scope_table.records[name]
                else:
                    if idx == 0 and self.current_scope[-1] != 'global' and scope_rec is not None and scope_rec.member_of is not None:
                        class_table = self.global_table.records.get(scope_rec.member_of)
                        if class_table is None:
                            error = SemanticError(
                                f'Scope {scope_rec.member_of} can not be resolved (line: {scope_rec.position})'
                            )
                        else:
                            if name in class_table.table_link.records.keys():
                                # in class scope, from function in class scope
                                record = class_table.table_link.records[name]
                            else:
                                # not in class scope
                                error = SemanticError(
                                    f'Undeclared data member "{name}" for class {scope_rec.member_of} (line: {base.token.position})'
                                )
                    elif idx != 0 and len(types) > 0:
                        scope_name = types[-1].type.type_name
                        if scope_name == 'void':
                            error = SemanticError(
                                f'Accessing member variable of VOID (line: {base.token.position})'
                            )
                        elif scope_name not in self.global_table.records.keys():
                            if TypeEnum.is_class(scope_name):
                                error = SemanticError(
                                    f'Accessing member variable of undefined class {scope_name} (line: {base.token.position})'
                                )
                            else:
                                error = SemanticError(
                                    f'Accessing member variable of non-class type {scope_name} (line: {base.token.position})'
                                )
                        else:
                            class_table = self.global_table.records[scope_name]
                            if name in class_table.table_link.records.keys():
                                record = class_table.table_link.records[name]
                            else:
                                error = SemanticError(
                                    f'Undeclared data member "{name}" for class {scope_name} (line: {base.token.position})'
                                )
                    else:
                        # global scope or function scope and it was not found here
                        error = SemanticError("Undeclared variable {} (accessed at line: {})".format(
                            name,
                            base.token.position
                        ))
                if record is not None:
                    # TODO check for access modifiers
                    if record.member_of is not None and scope_rec.member_of is None:
                        # class member is being accessed from outside class scope
                        if record.visibility == Visibility.Private:
                            error = SemanticError(
                                f'Variable {name} is declared private but being accessed outside class scope (line: {base.token.position})'
                            )
                    # have the record
                    type_rec = TypeRecord(
                        record.type,
                        is_array=record.is_array,
                        dimensions=record.dimensions
                    )
                    type_rec.position = base.token.position
                    types.append(type_rec)
                    # now validate do the type checking
                    if len(comps[list_idx].indices) == 0 or (len(comps[list_idx].indices) == record.dimensions):
                        # dimensions are the same or it's not an array
                        # simply the type
                        if len(comps[list_idx].indices) == record.dimensions:
                            for idx_node in comps[list_idx].indices:
                                if idx_node.type_rec.type.enum != TypeEnum.Integer:
                                    if error is not None:
                                        self.errors.append(error)
                                    error = SemanticError(
                                        'Array index is of invalid type {} -- integers are the only valid array index {}'.format(
                                            idx_node.type_rec.type.type_name,
                                            f'(line: {base.token.position})'
                                        )
                                    )
                    elif not record.is_array:
                        # problem!!!
                        error = SemanticError(f'Variable {name} is not subscriptable (line: {base.token.position})')
                    else:
                        # problem
                        error = SemanticError(
                            f'Variable {name} is an array of {record.dimensions} dimensions (line: {base.token.position})')
                if error is not None:
                    # there was an error
                    self.errors.append(error)
                elif record is None:
                    # raise RuntimeError('Error')
                    # there's a big issue here
                    pass
            else:
                # this is executed when function is at the front
                # function list is AParamList
                # if it's a function, need to look up function, get its return type
                # validate params list
                if idx != 0:
                    if len(types) != idx:
                        func_scopes = self.current_scope
                    else:
                        func_owner = types[idx - 1]
                        func_scopes = ['global', func_owner.type.type_name]
                else:
                    func_scopes = self.current_scope
                    if scope_rec is not None and scope_rec.member_of is not None and scope_rec.member_of in self.global_table.records.keys():
                        func_scopes.append(scope_rec.member_of)
                param_types = [param.type_rec for param in comps[list_idx].params]
                not_found = True
                scope_counter = -1
                while abs(scope_counter) < (len(func_scopes) + 1):
                    tmp_scope_name = func_scopes[scope_counter]
                    tmp_scope_rec = None if tmp_scope_name == 'global' else self.global_table.records.get(tmp_scope_name)
                    if tmp_scope_rec is not None or tmp_scope_name == 'global':
                        tmp_scope_table = self.global_table if tmp_scope_name == 'global' else tmp_scope_rec.table_link
                        if tmp_scope_table.is_func_in_records(name):
                            func_rec = tmp_scope_table.match_func_call(name, param_types)
                            if func_rec is not None:
                                not_found = False
                                types.append(TypeRecord(func_rec.type))
                                break
                    scope_counter -= 1
                if not_found:
                    if TypeEnum.is_class(func_scopes[-1]):
                        error = SemanticError(
                            'Function with signature {} does not exist (called at line: {})'.format(
                                SymbolTable.get_func_signature(name, param_types=param_types, member_of_name=func_scopes[-1]),
                                base.token.position
                            )
                        )
                    elif func_scopes[-1] != 'main':
                        error = SemanticError(
                            'Cannot call function {} on non-class type {} (called at line: {})'.format(
                                name,
                                func_scopes[-1],
                                base.token.position
                            )
                        )
                    else:
                        error = SemanticError(
                            'Cannot call undefined function {} (called at line: {})'.format(
                                SymbolTable.get_func_signature(name, param_types=param_types, member_of_name=None),
                                base.token.position
                            )
                        )
                    self.errors.append(error)
        # the type of the node is the type at the end of the chain
        node.type_rec = types[-1] if len(types) > 0 else None

