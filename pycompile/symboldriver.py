import argparse
from pathlib import Path
from os.path import dirname, join as path_join, realpath

from pycompile.parser.parser import Parser
from pycompile.symbol.visitor import SemanticTableBuilder, TypeChecker


def analyze_test_file(input_file: Path, output_dir: str):
    print(f'   Parsing source file: {input_file}')
    error_name = path_join(output_dir, f'{input_file.stem}.outsemanticerrors')
    table_name = path_join(output_dir, f'{input_file.stem}.outsymboltables')

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

    all_errors = []
    for error in stb.errors + tc.errors:
        if 'line: ' not in error.args[0]:
            all_errors.append((1000000, error.args[0]))
        else:
            all_errors.append((int(error.args[0].split('line: ')[1].split(')')[0]), error.args[0]))
    sorted_errors = sorted(all_errors, key=lambda x: x[0])
    with open(error_name, 'w') as f:
        for error in sorted_errors:
            f.write(error[1] + '\n')

    arr_rep = stb.global_table.get_repr()
    with open(table_name, 'w') as f:
        for row in arr_rep:
            f.write(row + '\n')


def run_tests(test_dir: str, output_dir: str):
    print('Testing Parser...')
    print(f'Using dir: {test_dir}')
    print(f'Outputting to: {output_dir}')
    for test_file in Path(test_dir).iterdir():
        # if test_file.suffix == '.src' and test_file.stem == 'indices_test':
        # if test_file.suffix == '.src' and test_file.stem == 'polynomial':
        # if test_file.suffix == '.src' and test_file.stem == 'inheritance_scoping':
        # if test_file.suffix == '.src' and test_file.stem == 'polynomial_semantic_errors':
        # if test_file.suffix == '.src' and test_file.stem == 'overriding':
        # if test_file.suffix == '.src' and test_file.stem == 'bubblesort':
        # if test_file.suffix == '.src' and test_file.stem == 'class_func':
        #
        if test_file.suffix == '.src':
            analyze_test_file(test_file, output_dir)


def main(test_dir: str = None, output_dir: str = None):
    if test_dir is None:
        test_dir = path_join(dirname(realpath(__file__)), 'parser', 'tests', 'in')
    if output_dir is None:
        output_dir = path_join(dirname(realpath(__file__)), 'parser', 'tests', 'out')
    run_tests(test_dir, output_dir)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--test_dir', '-td', help='Directory to look for .src files in', default=None)
    ap.add_argument('--output_dir', '-od', help='Directory to place output files in', default=None)
    args = ap.parse_args()
    main(args.test_dir, args.output_dir)