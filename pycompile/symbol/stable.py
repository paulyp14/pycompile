from __future__ import annotations
from collections import OrderedDict
from typing import Dict, List, Union

from pycompile.symbol.error import SemanticWarning
from pycompile.symbol.record import SemanticRecord, Kind, TypeRecord, TypeEnum


class SymbolTable:
    def __init__(self, table_name):
        self.name = table_name
        self.records: Dict[str, SemanticRecord] = OrderedDict()
        self.matched = False
        self.duplicated_generator: dict = {}
        self.req_mem: int = 0

    def compute_size(self, computer, first_pass: bool):
        self.req_mem = 0
        for record in self.records.values():
            if record.kind in (Kind.Variable, Kind.Parameter):
                self.req_mem += computer.compute_from_record(record, first_pass)

    def generate_duplicated_param_name(self, record: SemanticRecord) -> str:
        if record.get_name() not in self.duplicated_generator.keys():
            self.duplicated_generator[record.get_name()] = 0
        self.duplicated_generator[record.get_name()] += 1
        return f'{record.name}{self.duplicated_generator[record.get_name()]}'

    def add_record(self, record: SemanticRecord, duplicated_name_key: str = None):
        name = record.get_name() if duplicated_name_key is None else duplicated_name_key
        self.records[name] = record

    def add_inherited_variable(self, record: SemanticRecord):
        self.records[record.get_name()] = record

    def add_inherited_function(self, record: SemanticRecord):
        class_funcs = [
            class_rec.get_func_decl().split('::')[1]
            for class_rec in self.records.values()
            if class_rec.kind == Kind.Function and class_rec.member_of == self.name
        ]
        func_dl = record.get_func_decl().split('::')[1]
        if func_dl not in class_funcs:
            self.records[func_dl] = record

    def already_defined(self, record: SemanticRecord) -> bool:
        return record.get_name() in self.records.keys() and (record.kind != Kind.Function or record.func_equality(self.records[record.get_name()]))

    def overloaded(self, record: SemanticRecord) -> bool:
        return record.get_name() in self.get_pre_ol_func_names() and record.kind == Kind.Function

    def was_overloaded(self, record: SemanticRecord) -> bool:
        return record.get_name() not in self.records.keys() and record.kind == Kind.Function

    def get_pre_ol_func_names(self) -> List[str]:
        names = [record.get_name().split('(')[0] for record in self.records.values() if record.kind == Kind.Function]
        return names

    def get_overloaded(self, record: SemanticRecord) -> str:
        names = [rec.get_func_decl() for rec in self.records.values() if rec.get_name() == record.get_name()]
        return names[0]

    def add_overloaded_record(self, record: SemanticRecord):
        if record.get_name() in self.records.keys():
            single_rec = self.records.pop(record.get_name())
            self.records[single_rec.get_func_decl()] = single_rec
        self.records[record.get_func_decl()] = record

    def get_overloaded_name(self, record: SemanticRecord) -> str:
        if record.get_name() in self.records.keys():
            return record.get_name()
        else:
            return record.get_func_decl()

    def find_shadowed_vars(self, outer_table, warnings, for_classes: bool = False, global_table: SymbolTable = None, inherit_checks: dict = None):
        for record in self.records.values():
            pos_msg = f'(line: {record.position})'
            decl = None
            if record.name in outer_table.records.keys() and record.name not in self.duplicated_generator.keys():
                if inherit_checks is None or not inherit_checks.get(self.name, {'done': False})['done']:
                    warnings.append(SemanticWarning(
                        f'Name {record.name} in scope {self.name} shadows a name from an outer scope {pos_msg}'
                    ))
            if record.kind == Kind.Function and self.name == record.member_of:
                # check for function overrides!!
                decl = record.get_func_decl()
                if '::' in decl:
                    decl = decl.split('::')[1]
                if decl in outer_table.records.keys():
                    func_name = record.get_name()
                    override_name = outer_table.records[decl].get_name()
                    override_msg = f'Overriding function {override_name} with function {func_name} {pos_msg}'
                    if not any([w.args[0] == override_msg for w in warnings]):
                        if inherit_checks is None or not inherit_checks[self.name]['done']:
                            warnings.append(SemanticWarning(override_msg))

            rec_name = record.name if decl is None else decl
            # add an entry
            outer_table.records[rec_name] = record
        # add outer records here
        for record in outer_table.records.values():
            if (for_classes and record.kind in (Kind.Function, Kind.Variable)) and record.member_of is not None and record.member_of != self.name:
                class_name = self.name
                class_table: SymbolTable = global_table.records[class_name].table_link
                if record.kind == Kind.Variable:
                    class_table.add_inherited_variable(record)
                elif record.kind == Kind.Function:
                    class_table.add_inherited_function(record)
        # now all entries processed, outer table contains outer names plus all these names
        # go back through the records and process the other entries
        for record in self.records.values():
            if record.table_link is not None:
                new_outer = SymbolTable('outer')
                for inner_rec in outer_table.records.values():
                    # if inner_rec.kind != Kind.Function or inner_rec.member_of is not None:
                    if inner_rec.kind != Kind.Function or inner_rec.member_of is None:
                        new_outer.add_record(inner_rec)
                    else:
                        new_outer.add_inherited_function(inner_rec)
                for_classes = True if record.kind == Kind.InheritanceRelation else False
                record.table_link.find_shadowed_vars(new_outer, warnings, for_classes=for_classes, global_table=global_table, inherit_checks=inherit_checks)
                if for_classes and inherit_checks is not None and record.kind == Kind.InheritanceRelation:
                    rec_name = record.table_link.name
                    if not inherit_checks[rec_name]['done']:
                        inherit_list = global_table.records.get(rec_name).inheritances if global_table.records.get(rec_name).inheritances is not None else []
                        if len(inherit_list) == 0:
                            print('\n   ******* WARNING: no inheritances list when checking inheritance.... *********\n')
                        inherit_checks[rec_name]['list'].append(self.name)
                        inherit_checks[rec_name]['done'] = all([inherit_name in inherit_checks[rec_name]['list'] for inherit_name in inherit_list])


    def match_func_call(self, name: str, params: List[TypeRecord]) -> Union[SemanticRecord, None]:
        match = None
        # get functions only
        potential_funcs = [rec for rec in self.records.values() if rec.kind == Kind.Function and rec.name == name]
        for rec in potential_funcs:
            declared_params = [frec for frec in rec.table_link.records.values() if frec.kind == Kind.Parameter]
            if len(params) == len(declared_params):
                match_able = True
                for param, declared_param in zip(params, declared_params):
                    declared_param: SemanticRecord
                    if (
                        param is None or param.type is None or
                        not TypeEnum.match(param.type.enum, declared_param.type.enum) or
                        param.is_array != declared_param.is_array or
                        (
                            (param.dimensions is None and declared_param.dimensions != 0) or
                            (param.dimensions != declared_param.dimensions)
                        )
                    ):
                        match_able = False
                        break
                if match_able:
                    match = rec
                    break
        return match

    def is_func_in_records(self, func_name) -> bool:
        for name, func in self.records.items():
            if func.kind != Kind.Function:
                continue
            if func_name in name:
                return True
        return False


    @staticmethod
    def get_func_signature(name: str, param_types: List[TypeRecord] = None, member_of_name: str = None):
        member_of_name = f'{member_of_name}::' if member_of_name is not None else ''
        name = f'{member_of_name}{name}'
        if param_types is not None:
            param_strs = [str(t) for t in param_types]
            params = f'({", ".join(param_strs)})'
            name += params
        return name

    def max_len(self, pad: int = 0, class_rec = None) -> int:
        lengths = []
        has_table_children = False
        for value in self.records.values():
            if self.name == 'global' and value.member_of is not None:
                continue
            if class_rec is not None and value.member_of != class_rec.name:
                continue
            lengths.append(value.get_length())
            if value.table_link is not None:
                if not has_table_children:
                    has_table_children = True
                cur_class = None if value.kind != Kind.Class else value
                lengths.append(value.table_link.max_len(pad=(pad + 6), class_rec=cur_class))
        if class_rec is not None and class_rec.inheritances is not None and len(class_rec.inheritances) > 0:
            lengths.append(len(f' inherit   | {", ".join(class_rec.inheritances)}'))
        lengths.append(len(f' table: {self.name} '))
        return max(lengths) + (8 if has_table_children else + 2)

    def get_repr(self, left_pad: int = 0, right_pad: int = 0, parent_length: int = 0, class_rec=None) -> List[str]:
        rows = []
        level_length = self.max_len()
        row_pad = (parent_length - level_length) * ' '
        for value in self.records.values():
            if self.name == 'global' and value.member_of is not None:
                continue
            if class_rec is not None and value.member_of != class_rec.name:
                continue
            rows.extend(value.array_repr(min_len=level_length))
            if value.table_link is not None:
                cur_class = None if value.kind != Kind.Class else value
                rows.extend(value.table_link.get_repr(left_pad=4, right_pad=2, parent_length=level_length - 8, class_rec=cur_class))
        table_name_row = ' table: ' + self.name + ' '
        table_name_row = f'{table_name_row}{(level_length - len(table_name_row)) * " "}'
        if class_rec is not None and class_rec.inheritances is not None and len(class_rec.inheritances) > 0:
            inherit_row = f' inherit   | {", ".join(class_rec.inheritances)}'
            inherit_row = f'{inherit_row}{(level_length - len(inherit_row)) * " "}'
            rows = [inherit_row] + rows
        rows = [table_name_row] + rows
        rows = [f'|{row}{row_pad}|' for row in rows]
        if parent_length != 0:
            sepr = (level_length + (parent_length - level_length) + 2) * '='
        else:
            sepr = (level_length + 2) * '='
        rows = [sepr] + [rows[0]] + [sepr] + rows[1:] + [sepr]
        # do other processing steps
        if right_pad != 0 or left_pad != 0:
            new_rows = []
            for row in rows:
                right_str = right_pad * ' '
                left_str = left_pad * ' '
                row = f'{left_str}{row}{right_str}'
                new_rows.append(row)
            rows = new_rows
        return rows







