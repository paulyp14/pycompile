import argparse
from pathlib import Path

from pycompile.compiler import PyCompiler


def compile_file(input_file, enable_output, output_location, test_location):

    compiler = PyCompiler(enable_output, output_location, test_location)
    compiler.compile(input_file)


def main(enable_output, output_location, test_output, to_compile, is_dir):
    if is_dir:
        for test_file in Path(to_compile).iterdir():
            if test_file.suffix == '.src':
                compile_file(test_file.as_posix(), enable_output, output_location, test_output)
    else:
        compile_file(to_compile, enable_output, output_location, test_output)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--enable_output', action='store_true')
    ap.add_argument('--output_location', default='.')
    ap.add_argument('--test_output', default=None)
    ap.add_argument('--to-compile')
    ap.add_argument('--is-dir', action='store_true')
    args = ap.parse_args()

    main(args.enable_output, args.output_location, args.test_output, args.to_compile, args.is_dir)