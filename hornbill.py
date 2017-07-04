import argparse

import validate


if __name__ == "__main__":
    acceptable_types = {'edt', 'doxygen'}

    parser = argparse.ArgumentParser()
    parser.add_argument('--comment-check',
                      metavar="FILENAME(S)",
                      nargs="+",
                      help='C file in which to validate comments')

    parser.add_argument('--ignore-funcs',
                      metavar="FILENAME",
                      help='A newline delimited file containing function names'
                      ' to ignore while validating docstrings')

    args = parser.parse_args()

    if args.ignore_funcs:
        with open(args.ignore_funcs) as f:
            ignore_func_list = [x.strip() for x in f.readlines()]
    else:
        ignore_func_list = list()

    if args.comment_check:
        errors = list()
        for filename in args.comment_check:
            errors.extend(validate.find_documentation_errors(filename))

        for err in errors:
            if err.func.name not in ignore_func_list:
                err.print_err()
