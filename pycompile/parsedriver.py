import argparse
from pathlib import Path
from os.path import dirname, join as path_join, realpath

from pycompile.parser.parser import Parser


def analyze_test_file(input_file: Path, output_dir: str):
    print(f'   Parsing source file: {input_file}')
    deriv_name = path_join(output_dir, f'{input_file.stem}.outderivation')
    stack_name = path_join(output_dir, f'{input_file.stem}.outstack')
    ast_name = path_join(output_dir, f'{input_file.stem}.outast')
    err_name = path_join(output_dir, f'{input_file.stem}.outerrors')
    ast_gv_name = path_join(output_dir, f'{input_file.stem}.outast.gv')

    parser = Parser("Table")

    with open(str(input_file), 'r') as f:
        data = f.read()

    ast, stack_cont, errors, deriv = parser.run(data)

    with open(deriv_name, 'w') as f:
        for line in deriv:
            f.write(f'{line}\n')

    with open(ast_name, 'w') as f:
        for line in ast:
            f.write(f'{line}\n')

    with open(err_name, 'w') as f:
        for line in errors:
            f.write(f'{line}\n')

    with open(stack_name, 'w') as f:
        for line in stack_cont:
            f.write(f'{line}\n')

    parser.gv_ast.render(ast_gv_name)


def run_tests(test_dir: str, output_dir: str):
    print('Testing Parser...')
    print(f'Using dir: {test_dir}')
    print(f'Outputting to: {output_dir}')
    for test_file in Path(test_dir).iterdir():
        # if test_file.suffix == '.src' and test_file.stem == 'indices_test':
        # if test_file.suffix == '.src' and test_file.stem == 'bubblesort':
        # if test_file.suffix == '.src' and test_file.stem == 'class_func':
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
