import os
import sys
from pathlib import Path
from typing import Optional, Union, List

from pycompile.parser.parser import Parser
from pycompile.symbol.error import SemanticError
from pycompile.codegenr.generator import CodeGenerator
from pycompile.parser.syntax.collector import Collector
from pycompile.codegenr.allocator import MemoryAllocator
from pycompile.symbol.visitor import SemanticTableBuilder, TypeChecker


class PyCompiler:

    def __init__(self, enable_output: bool = False, output_location: Union[str, Path] = '.', test_output: str = None):
        self.enable_output: bool = enable_output
        self.output_location: Path = output_location if isinstance(output_location, Path) else Path(output_location)
        self.output_name: Optional[str] = None
        self.output_dir: Optional[Path] = None
        self.test_output: Optional[str] = None

        self.parser: Parser = Parser("Table")
        self.sym_table_builder: SemanticTableBuilder = SemanticTableBuilder()
        self.type_checker: TypeChecker = None
        self.mem_allocator: MemoryAllocator = None
        self.code_generator: CodeGenerator = None
        self.code: Optional[str] = None

    def __error_print(self, exception: Exception, step_name: str):
        msg = f'    Encounter unexpected exception\n{exception.__class__.__name__}: {exception.args[0]}'
        msg_two = f'    {step_name} step could not be completed'
        self.__eprint(msg)
        self.__eprint(msg_two)

    def __eprint(self, msg: str):
        print(msg, file=sys.stderr)

    def compile(self, to_compile: Union[Path, str]):
        if isinstance(to_compile, Path) or (Path(to_compile).exists() and Path(to_compile).is_file()):
            with open(str(to_compile), 'r') as src_file:
                self.code = src_file.read()
            if not isinstance(to_compile, Path):
                to_compile = Path(to_compile)
            self.output_name = str(to_compile.stem)
        else:
            self.code = to_compile
            self.output_name = 'inline'
            to_compile = '( inline code )'
        # set up for output
        self.output_dir = self.output_location if not self.enable_output else Path(os.path.join(str(self.output_location), self.output_name))

        last_step_success = True

        print('===============================================')
        print(f'\n Compiling file: {to_compile}')
        # parse the program
        try:
            self.parser.parse(self.code)
            print('    Parsing complete')
        except Exception as e:
            last_step_success = False
            self.__error_print(e, 'Parsing')

        # check for errors
        if last_step_success:
            # do the symbol table generation
            try:
                self.parser.traverse(self.sym_table_builder)
                last_step_success = not any([
                    isinstance(sem_err, SemanticError)
                    for sem_err in self.sym_table_builder.errors
                ])
                print('    Symbol table created')
            except Exception as e:
                last_step_success = False
                self.__error_print(e, 'SymbolTableCreator')

        if last_step_success:
            # do the typeChecking table generation
            try:
                self.type_checker = TypeChecker(self.sym_table_builder.global_table, self.sym_table_builder.errors)
                self.parser.traverse(self.type_checker)
                last_step_success = not any([
                    isinstance(sem_err, SemanticError)
                    for sem_err in self.sym_table_builder.errors
                ])
                print('    Type checking performed')
            except Exception as e:
                last_step_success = False
                self.__error_print(e, 'TypeChecker')

        self.__print_semantic_errors(last_step_success)

        if last_step_success:
            # do the memory allocation
            try:
                self.mem_allocator = MemoryAllocator(self.type_checker.global_table)
                self.parser.traverse(self.mem_allocator)
                print('    Memory allocation complete')
            except Exception as e:
                last_step_success = False
                self.__error_print(e, 'MemoryAllocation')

        if last_step_success:
            # do the code generation
            try:
                self.code_generator = CodeGenerator(self.mem_allocator.global_table)
                self.parser.traverse(self.code_generator)
                print('    Code generation complete')
            except Exception as e:
                last_step_success = False
                self.__error_print(e, "CodeGeneration")

        if self.enable_output:
            self.__output()
        # always need to output the generated code or else what good is it...
        if self.code_generator is not None:
            code_name = f'{os.path.join(str(self.output_dir), self.output_name)}.moon'
            # output generated code
            with open(code_name, 'w') as f:
                for code in self.code_generator.code_stream + self.code_generator.data_stream:
                    f.write(code + '\n')
            # output to another dir if specified
            if self.test_output is not None:
                test_name = f'{os.path.join(self.test_output, self.output_name)}.moon'
                with open(test_name, 'w') as f:
                    for code in self.code_generator.code_stream + self.code_generator.data_stream:
                        f.write(code + '\n')
            print(f'    Generated code output to: {code_name}')
        if last_step_success:
            print(' COMPILE SUCCESS')
        print('===============================================\n')
    def __output(self):
        if not self.output_dir.exists():
            self.output_dir.mkdir()
        base_name = os.path.join(str(self.output_dir), self.output_name)
        if self.parser is not None:
            token_name = f'{base_name}.outlextokens'
            error_name = f'{base_name}.outlexerrors'
            deriv_name = f'{base_name}.outderivation'
            stack_name = f'{base_name}.outstack'
            ast_name = f'{base_name}.outast'
            parse_err = f'{base_name}.outerrors'
            # output stuff from A1
            self.parser.parser.analyzer.write_tokenized(token_name)
            self.parser.parser.analyzer.write_errors(error_name)
            # output stuff from A2
            collector = Collector()
            collector.collect(self.parser.ast)
            collector.grph.render(ast_name)

            with open(deriv_name, 'w') as f:
                for line in self.parser.derivation:
                    f.write(f'{line}\n')
            with open(parse_err, 'w') as f:
                for error in self.parser.parser.errors:
                    f.write(f'{error.message}\n')
            with open(stack_name, 'w') as f:
                for line in self.parser.stack_contents:
                    f.write(f'{line}\n')

        if self.sym_table_builder is not None:
            sem_err_name = f'{base_name}.outsemanticerrors'
            with open(sem_err_name, 'w') as f:
                for error in self.__get_semantic_errors():
                    f.write(f'{error[1]}\n')

        if self.mem_allocator is not None:
            sym_tab_name = f'{base_name}.outsymboltables'
            with open(sym_tab_name, 'w') as f:
                for row in self.mem_allocator.global_table.get_repr():
                    f.write(f'{row}\n')

    def __print_semantic_errors(self, last_step_success: bool):
        if not last_step_success:
            self.__eprint('Could not compile because of semantic errors!\n')
        for error in self.__get_semantic_errors():
            self.__eprint(error[1])

    def __get_semantic_errors(self) -> List[tuple]:
        all_errors = []
        for error in (self.sym_table_builder.errors if self.type_checker is None else self.type_checker.errors):
            if 'line: ' not in error.args[0]:
                pos = 1000000
            else:
                pos = int(error.args[0].split('line: ')[1].split(')')[0])
            msg = f'{error.__class__.__name__}: {error.args[0]}'
            all_errors.append((pos, msg))
        return sorted(all_errors, key=lambda x: x[0])
