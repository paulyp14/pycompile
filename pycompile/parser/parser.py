from typing import Union
from pathlib import Path

from pycompile.parser.strategy.helper import Table
from pycompile.parser.strategy.table import TableParser
from pycompile.parser.strategy.strategy import ParsingStrategy
from pycompile.parser.strategy.recursive import RecursiveDescentParser


class Parser:

    def __init__(self,
                 strategy: str = "Recursive",
                 code: str = None,
                 grammar: str = None,
                 grammar_file: Union[Path, str] = None,
                 optional: dict = None):
        self.strategy: str = strategy

        if self.strategy == 'Recursive':
            self.parser: ParsingStrategy = RecursiveDescentParser(code)
        else:
            table = Table.create(grammar=grammar, grammar_file=grammar_file, optional=optional)
            table.fill_errors()
            self.parser: ParsingStrategy = TableParser(code, table)

    def parse(self, code: str = None):
        self.parser.parse(code)
