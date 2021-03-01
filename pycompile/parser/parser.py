from pycompile.parser.strategy.table import TableParser
from pycompile.parser.strategy.strategy import ParsingStrategy
from pycompile.parser.strategy.recursive import RecursiveDescentParser


class Parser:

    def __init__(self, strategy: str = "Recursive", code: str = None):
        self.strategy: str = strategy

        if self.strategy == 'Recursive':
            self.parser: ParsingStrategy = RecursiveDescentParser(code)
        else:
            self.parser: ParsingStrategy = TableParser(code)

    def parse(self, code: str = None):
        self.parser.parse(code)
