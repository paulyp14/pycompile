import argparse
from pathlib import Path
from os.path import dirname, join as path_join, realpath

from pycompile.parser.parser import Parser
from pycompile.codegenr.generator import CodeGenerator
from pycompile.codegenr.allocator import MemoryAllocator
from pycompile.symbol.visitor import SemanticTableBuilder, TypeChecker


def analyze_test_file(input_file: Path, output_dir: str):
    print(f'   Parsing source file: {input_file}')
    moon_name = path_join(output_dir, f'{input_file.stem}.moon')

    parser = Parser("Table")

    with open(str(input_file), 'r') as f:
        data = f.read()

    parser.parse(data)
    # build symbol tables
    stb = SemanticTableBuilder()
    parser.traverse(stb)
    # type check, use Symbol table that was already created and add to existing errors
    tc = TypeChecker(stb.global_table, None)
    parser.traverse(tc)

    alloc = MemoryAllocator(tc.global_table)
    parser.traverse(alloc)

    gnrtr = CodeGenerator(alloc.global_table)
    parser.traverse(gnrtr)

    with open(moon_name, 'w') as f:
        for code in gnrtr.code_stream + gnrtr.data_stream:
            f.write(code + '\n')

    with open(f'C:\\Users\\flyin\\Projects\\Concordia\\comp-442\\moon\\test_files\\{input_file.stem}.moon', 'w') as f:
        for code in gnrtr.code_stream + gnrtr.data_stream:
            f.write(code + '\n')


def run_tests(test_dir: str, output_dir: str):
    print('Testing Parser...')
    print(f'Using dir: {test_dir}')
    print(f'Outputting to: {output_dir}')
    for test_file in Path(test_dir).iterdir():
        # if test_file.suffix == '.src' and test_file.stem == 'allocation':
        # if test_file.suffix == '.src' and test_file.stem == 'simple_while':
        # if test_file.suffix == '.src' and test_file.stem == 'simple_main':
        # if test_file.suffix == '.src' and test_file.stem == 'read_test':
        # if test_file.suffix == '.src' and test_file.stem == 'array_access':
        # if test_file.suffix == '.src' and test_file.stem == 'function_calls':
        # if test_file.suffix == '.src' and test_file.stem == 'simple_test':
        # if test_file.suffix == '.src' and test_file.stem == 'bubblesort':
        # if test_file.suffix == '.src' and test_file.stem == 'bubblesort_recursive':
        # if test_file.suffix == '.src' and test_file.stem == 'division_test':
        # if test_file.suffix == '.src' and test_file.stem == 'member_functions':
        if test_file.suffix == '.src':
            analyze_test_file(test_file, output_dir)


def main(test_dir: str = None, output_dir: str = None):
    if test_dir is None:
        test_dir = path_join(dirname(realpath(__file__)), 'codegenr', 'tests', 'in')
    if output_dir is None:
        output_dir = path_join(dirname(realpath(__file__)), 'codegenr', 'tests', 'out')
    run_tests(test_dir, output_dir)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--test_dir', '-td', help='Directory to look for .src files in', default=None)
    ap.add_argument('--output_dir', '-od', help='Directory to place output files in', default=None)
    args = ap.parse_args()
    main(args.test_dir, args.output_dir)