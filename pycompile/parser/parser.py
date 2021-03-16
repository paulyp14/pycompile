from pathlib import Path
from typing import List, Tuple, Union

from pycompile.parser.strategy.helper import Table
from pycompile.parser.strategy.table import TableParser
from pycompile.parser.strategy.strategy import ParsingStrategy
from pycompile.parser.strategy.recursive import RecursiveDescentParser
from pycompile.parser.syntax.ast import AbstractSyntaxNode
from pycompile.parser.syntax.collector import Collector


class Parser:

    def __init__(self,
                 strategy: str = "Recursive",
                 code: str = None,
                 grammar: str = None,
                 grammar_file: Union[Path, str] = None,
                 optional: dict = None):
        self.success: bool = False
        self.strategy: str = strategy
        self.ast: Union[AbstractSyntaxNode, None] = None
        self.derivation: List[str] = None
        self.stack_contents: List[str] = None

        parent = Path(__file__).parent
        self.default_config = {
            'calgaryTableFile': f'{parent}/grammar_files/ucalgary_parse_table.html',
            'calgaryFirstAndFollow': f'{parent}/grammar_files/ucalgary_first_follow.html',
            'grammar_file': f"{parent}/grammar_files/LL1.paquet.grm"
        }

        if self.strategy == 'Recursive':
            self.parser: ParsingStrategy = RecursiveDescentParser(code)
        else:
            grammar_file = grammar_file if grammar_file is not None else self.default_config['grammar_file']
            optional = optional if optional is not None else self.default_config
            table = Table.create(grammar=grammar, grammar_file=grammar_file, optional=optional)
            table.fill_errors()
            table.validate_semantic_actions()
            self.parser: ParsingStrategy = TableParser(code, table)

    def parse(self, code: str = None):
        self.success, self.ast, self.stack_contents, self.derivation = self.parser.parse(code)

    def run(self, code: str) -> Tuple[List[str], List[str], List[str], List[str]]:
        self.parse(code)
        # collect printable ast
        collector = Collector()
        collector.collect(self.ast)
        errors = [e.message for e in self.parser.errors]
        return collector.create_array_repr(), self.stack_contents, errors, self.derivation


