import argparse

from edt import gen_edt
from doxygen import gen_doxygen, gen_doxygen_snippet
from formatter import format_func
from c_parser import parse_file_functions
from validate import find_documentation_errors


if __name__ == "__main__":
    acceptable_types = {'edt', 'doxygen'}

    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--comment-check',
                      help='C file in which to validate comments')
    mode.add_argument('--type',
                      help='edt or doxygen',
                      choices=acceptable_types)
    mode.add_argument('--format',
                      action='store_true',
                      help='Format the function nicely.')

    parser.add_argument('--file', help='C file to examine',
                        required=False)
    parser.add_argument('--line',
                        help='Line number of function name',
                        type=int,
                        required=False)
    parser.add_argument('--debug',
                        help='Turn on debug mode',
                        action='store_true')


    args = parser.parse_args()
    if args.comment_check:
        errors = find_documentation_errors(args.comment_check)
        for err in errors:
            err.print_err()
        exit()

    if not args.file:
        raise InputError("file positional argument is required.")
    if not args.line:
        raise InputError("line positional argument is required.")

    func = parse_func(args.file, args.line)
    if args.debug:
        print(func)

    if args.format:
        print(format_func(func))
    else:
        if args.type == 'edt':
            print(gen_edt(func))
        elif args.type == 'doxygen':
            gen_doxygen_snippet(func)
        else:
            raise AssertionError("Unknown type {} received".format(args.type))
