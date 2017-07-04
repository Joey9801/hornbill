import argparse

import validate


if __name__ == "__main__":
    acceptable_types = {'edt', 'doxygen'}

    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--comment-check',
                      metavar="FILENAME(S)",
                      nargs="+",
                      help='C file in which to validate comments')

    args = parser.parse_args()
    if args.comment_check:
        errors = list()
        for filename in args.comment_check:
            errors.extend(validate.find_documentation_errors(filename))

        for err in errors:
            err.print_err()
