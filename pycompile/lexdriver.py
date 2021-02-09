from os.path import dirname, join as path_join, realpath
from pathlib import Path

from pycompile.lex.analyzer import LexicalAnalyzer


def analyze_test_file(input_file):
    print(f'   Analyzing file: {input_file}')
    token_name = f'{input_file.name}.outlextokens'
    error_name = f'{input_file.name}.outlexerrors'

    analyzer = LexicalAnalyzer()

    with open(str(input_file), 'r') as f:
        data = f.read()

    analyzer.tokenize(data)
    analyzer.write_tokenized(token_name)
    analyzer.write_errors(error_name)


def run_tests(test_dir: str):
    print('Testing LexicalAnalyzer...')
    print(f'   Using dir: {test_dir}')
    for test_file in Path(test_dir).iterdir():
        if test_file.suffix == '.src':
            analyze_test_file(test_file)


def main(test_dir=None):
    if test_dir is None:
        test_dir = path_join(dirname(realpath(__file__)), 'lex', 'tests')
    run_tests(test_dir)


if __name__ == '__main__':
    main()