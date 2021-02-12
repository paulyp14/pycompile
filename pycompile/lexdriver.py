import argparse
from pathlib import Path
from os.path import dirname, join as path_join, realpath

from pycompile.lex.analyzer import LexicalAnalyzer


def analyze_test_file(input_file: Path, output_dir: str):
    print(f'   Analyzing file: {input_file}')
    token_name = path_join(output_dir, f'{input_file.stem}.outlextokens')
    error_name = path_join(output_dir, f'{input_file.stem}.outlexerrors')

    analyzer = LexicalAnalyzer()

    with open(str(input_file), 'r') as f:
        data = f.read()

    analyzer.tokenize(data)
    analyzer.write_tokenized(token_name)
    analyzer.write_errors(error_name)


def run_tests(test_dir: str, output_dir: str):
    print('Testing LexicalAnalyzer...')
    print(f'Using dir: {test_dir}')
    print(f'Outputting to: {output_dir}')
    for test_file in Path(test_dir).iterdir():
        if test_file.suffix == '.src':
            analyze_test_file(test_file, output_dir)


def main(test_dir: str = None, output_dir: str = None):
    if test_dir is None:
        test_dir = path_join(dirname(realpath(__file__)), 'lex', 'tests')
    if output_dir is None:
        output_dir = path_join(dirname(realpath(__file__)), 'lex', 'tests')
    run_tests(test_dir, output_dir)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--test_dir', '-td', help='Directory to look for .src files in', default=None)
    ap.add_argument('--output_dir', '-od', help='Directory to place output files in', default=None)
    args = ap.parse_args()
    main(args.test_dir, args.output_dir)
