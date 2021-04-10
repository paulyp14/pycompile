from typing import List

from pycompile.symbol.stable import SymbolTable
from pycompile.symbol.record import SemanticRecord


class StackFrame:
    def __init__(self, symbol_table: SymbolTable):
        self.size: int = 0
        self.name: str = symbol_table.name
        self.table: SymbolTable = SymbolTable(symbol_table.name)

        for record in self.table.records.items():
            pass