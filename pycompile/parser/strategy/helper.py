from __future__ import annotations

import pandas as pd
from pathlib import Path
from typing import Dict, List, Union

from pycompile.lex.token import *


class Table:

    def __init__(self):
        self.terminals: List[Union[str, Token]] = []
        self.non_terminals: List[str] = []
        self.rules: Dict[str, Dict[str, List[str]]] = {}
        self.first_sets: Dict[str, List[str]] = {}
        self.follow_sets: Dict[str, List[str]] = {}
        self.parse_table: Dict[str, Dict[Union[str, Token]]] = {}
        self.mappings: Dict = {
            "id": Id,
            "intNum": Integer,
            "intLit": Integer,
            "floatLit": Float,
            "floatNum": Float,
            "stringLit": String,
            "intnum": Integer,
            "intlit": Integer,
            "floatlit": Float,
            "floatnum": Float,
            "stringlit": String,
            'leq': '<=',
            'sr': '::',
            'lt': '<',
            'gt': '>',
            'eq': '==',
            'and': '&',
            'or': '|',
            'neq': '<>',
            'qm': '?',
            'geq': '>=',
            'assign': '=',
            'not': '!',
            '$': Final
        }

        self.terminal_translations = {
            'ucalgary': {
                'intnum': 'intNum',
                'mult': '*',
                'lsqbr': '[',
                'rpar': ')',
                'floatnum': 'floatNum',
                'stringlit': 'stringLit',
                'minus': '-',
                'rsqbr': ']',
                'comma': ',',
                'plus': '+',
                'rcurbr': '}',
                'lcurbr': '{',
                'colon': ':',
                'dot': '.',
                'semi': ';',
                'lpar': '(',
                '&epsilon': 'EPSILON'
            }
        }

        self.rule_translations: Dict = {}
        self.type_lookup: Dict = {
            'Float': Float,
            'Integer': Integer,
            'Id': Id,
            'String': String
        }

    @staticmethod
    def create(grammar: str = None,
               optional: dict = None,
               grammar_file: Union[str, Path] = None) -> Table:
        """
        :param grammar: the grammar
        :param optional: first and follow sets
        :param grammar_file: file to load from instead
        :return:
        """
        table = Table()

        if grammar is not None:
            table.__parse_given_grammar(grammar)
        elif grammar_file is not None:
            table.__load(grammar_file)

        if optional is not None:
            table.__ingest_optional(optional)

        return table

    def __load(self, file: Union[str, Path]):
        with open(file, 'r') as g_f:
            grammar = g_f.read()
            self.__parse_given_grammar(grammar)

    def __ingest_optional(self, optional: dict):
        if 'calgaryTableFile' in optional.keys():
            self.load_calgary_table(optional['calgaryTableFile'])

        if 'calgaryFirstAndFollow' in optional.keys():
            self.load_calgary_first_follow(optional['calgaryFirstAndFollow'])

    def load_calgary_table(self, file_name: Union[str, Path]):
        if 'calgary' not in self.rule_translations.keys():
            self.translate_calgary(file_name)
        # use pandas to load table as df
        df = pd.read_html(file_name)[1]
        columns = df.iloc[0][2:]
        rows = df[0][1:]
        df = df.loc[1:, 2:]
        df.columns = columns
        df.index = rows
        for non_term, row in df.iterrows():
            trans = self.get_calgary_translated(non_term)
            for u_term, item in row.items():
                term = self.get_calgary_translated(u_term)
                if pd.isna(item):
                    continue
                rule_parts = list(map(
                    lambda x: self.get_calgary_translated(x),
                    item.split()[2:]
                ))
                if len(rule_parts) == 1 and rule_parts[0] == 'EPSILON':
                    rule_parts = []
                self.parse_table[trans][term] = rule_parts

    def get_calgary_translated(self, u_term) -> str:
        return self.get_translation('ucalgary', u_term)

    def get_translation(self, source: str, u_term: str) -> str:
        if u_term in self.rule_translations[source].keys():
            return self.rule_translations[source][u_term]
        else:
            first_trans = self.terminal_translations[source].get(u_term, u_term)
            return self.mappings.get(first_trans, first_trans)

    def translate_calgary(self, file_name: Union[str, Path]):
        mapping = {}
        temp_map = {}
        terms = set()
        df = pd.read_html(file_name)[0]
        for _, row in df.iterrows():
            if pd.isna(row[0]):
                continue
            rule = row[0].split()[0]
            rhs = row[1].split()[:-1]
            if len(rhs) == 0:
                rhs = ['EPSILON']
            if rule not in temp_map.keys():
                temp_map[rule] = []
            temp_map[rule].append(rhs)
            if rule not in mapping.keys():
                found = False
                for proper_rule in self.rules.keys():
                    if proper_rule.lower() == rule.lower():
                        found = True
                        mapping[rule] = proper_rule
                        break
            for item in rhs:
                if item.upper() != item:
                    terms.add(item)
        # add the map of non-terminals
        self.rule_translations['ucalgary'] = mapping
        print('Here')

    def load_calgary_first_follow(self, file_name: Union[str, Path]):
        # use pandas to load table as df
        df = pd.read_html(file_name)[2]
        for _, row in df.iterrows():
            trans = self.get_calgary_translated(row['nonterminal'])
            self.first_sets[trans] = self.extract_first(row)
            self.follow_sets[trans] = self.extract_follow(row)

    def extract_first(self, row: pd.Series) -> List[str]:
        return self.extract_set_from_row(row, 'first set')

    def extract_follow(self, row: pd.Series) -> List[str]:
        return self.extract_set_from_row(row, 'follow set')

    def extract_set_from_row(self, row: pd.Series, set_name: str) -> List[str]:
        # if 'EPSILON' in self.rules[non_term].keys() and row['nullable'] != 'yes':
        #     print('UHOH')
        # if 'EPSILON' not in self.rules[non_term].keys() and row['nullable'] == 'yes':
        #     print('UHOH')

        extra = ['EPSILON'] if row['nullable'] == 'yes' and set_name == 'first set' else []
        return [self.get_calgary_translated(x) for x in row[set_name].split() if x not in ['', '∅']] + extra

    def __parse_given_grammar(self, grammar: str):
        lines = grammar.split('\n')
        for line in lines:
            line = line.strip()
            if line == '':
                continue
            rule, expr = line.split(' ::= ')
            rule = rule[1:-1]

            if rule not in self.non_terminals:
                self.non_terminals.append(rule)
                self.__create(rule)

            lhs_toks = expr.split(' ')
            replacements = []
            removes = []
            # use_empty = False
            for i, lhs_tok in enumerate(lhs_toks):
                if lhs_tok == '':
                    removes.append(i)
                elif lhs_tok[0] == '<':
                    replacements.append((i, lhs_tok[1:-1]))
                elif lhs_tok[0] == "'":
                    lhs_tok = lhs_tok.replace("'", '')
                    lhs_tok = self.mappings.get(lhs_tok, lhs_tok)
                    if lhs_tok not in self.terminals:
                        self.terminals.append(lhs_tok)
                    replacements.append((i, lhs_tok))
                elif lhs_tok == 'EPSILON':
                    continue
                    # use_empty = True
                else:
                    raise RuntimeError('Something wrong')

            for idx, replacement in replacements:
                lhs_toks[idx] = replacement

            final_lhs = []
            if len(removes) > 0:
                for i, remove in enumerate(removes):
                    if i == 0:
                        final_lhs += lhs_toks[0:remove]
                    else:
                        final_lhs += lhs_toks[removes[i - 1] + 1: remove]
                    # if this is the last idx to remove
                    # and it is not the last idx of the original token list
                    if i + 1 == len(removes) and remove + 1 != len(lhs_toks):
                        # add the remaining tokens
                        final_lhs += lhs_toks[remove + 1:]
            else:
                final_lhs = lhs_toks

            self.rules[rule][expr] = final_lhs  # if not use_empty else []

        for non_terminal in self.non_terminals:
            for terminal in self.terminals:
                self.parse_table[non_terminal][terminal] = None

    def fill_errors(self):
        for non_terminal in self.non_terminals:
            for terminal in self.terminals:
                if self.parse_table[non_terminal][terminal] is None:
                    self.parse_table[non_terminal][terminal] = 'Error'

    def __create(self, rule: str):
        self.__check(rule, self.rules, dict)
        self.__check(rule, self.first_sets, list)
        self.__check(rule, self.follow_sets, list)
        self.__check(rule, self.parse_table, dict)

    def __check(self, k: str, d: dict, val_type):
        if k not in d.keys():
            d[k] = val_type()

    def get(self, non_term: str, terminal: Token):
        if isinstance(terminal, (Float, Integer, String, Id)):
            using = terminal.__class__.__name__
            using = self.type_lookup[using]
        else:
            using = terminal.lexeme
        return self.parse_table[non_term][using]


    def is_terminal(self, symbol: str) -> bool:
        return symbol not in self.rules.keys()

    def lookup(self, non_term: str, term: str) -> Union[List[Union[str, Token]], str]:
        return self.parse_table[non_term][term]

    def terminal_match(self, symbol: str, token: Token) -> bool:
        tok_mapping = self.mappings.get(symbol, symbol)
        if tok_mapping in self.type_lookup.values():
            return isinstance(token, tok_mapping)
        else:
            return token.lexeme == symbol

    def in_first(self, symbol: str, token: Token) -> bool:
        if isinstance(token, (Float, Integer, String, Id)):
            using = token.__class__.__name__
            using = self.type_lookup[using]
        else:
            using = token.lexeme
        return using in self.get_first_for_symbol(symbol)

    def in_follow(self, symbol: str, token: Token) -> bool:
        if isinstance(token, (Float, Integer, String, Id)):
            using = token.__class__.__name__
            using = self.type_lookup[using]
        else:
            using = token.lexeme
        return using in self.get_follow_for_symbol(symbol)

    def epsilon_in_first(self, symbol: str) -> bool:
        return 'EPSILON' in self.get_first_for_symbol(symbol)

    def get_first_for_symbol(self, symbol: Union[str, Token]) -> List:
        if isinstance(symbol, str) and symbol not in self.rules.keys():
            return [symbol]
        else:
            return self.first_sets[symbol]

    def get_follow_for_symbol(self, symbol: Union[str, Token]) -> List:
        if isinstance(symbol, str) and symbol not in self.rules.keys():
            return [symbol]
        else:
            return self.follow_sets[symbol]



