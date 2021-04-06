from pycompile.symbol.visitor import Visitor
from pycompile.symbol.stable import SymbolTable


class CodeGenerator(Visitor):

    def __init__(self, symbol_table: SymbolTable = None):
        super().__init__(symbol_table=symbol_table)
