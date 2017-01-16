#!/home/joe/Documents/independence_day/hornbill/python-venv/bin/python

from __future__ import print_function

import re
import sys
import json
import argparse
import tempfile
import linecache

from classes import *

from edt import gen_edt
from doxygen import gen_doxygen, gen_doxygen_snippet
from formatter import format_func

import clang.cindex
from clang.cindex import CursorKind

from parse_file_functions import parse_file_functions
from parse_doxygen import find_func_docstrings, CommentFormat


def parse_temp_stubbed(temp_filename):
    """
    Given a filename containing a single function declaration, parse it into a
    Function object
    """

    clang.cindex.Config.set_library_file('/usr/lib/llvm-3.8/lib/libclang.so.1')
    index = clang.cindex.Index.create()

    translation_unit = index.parse(temp_filename, ['-x', 'c'])

    # First clear up any errors of the form
    #   "unknown type name 'foo_t'"
    # We do this by adding fake types with lines like
    #   "typedef struct {} foo_t"
    # If we do not do this, the unknown types are substited with int's in the
    # AST, which is not what we want

    unknown_types = []
    for d in translation_unit.diagnostics:
        if d.severity == 3:
            quoted = re.compile("'([^']*)'")
            for value in quoted.findall(d.spelling):
                unknown_types.append(value)

    if len(unknown_types) > 0:
        unknown_typedefs = ["typedef int {};".format(x) for x in unknown_types]

        with open(temp_filename) as f:
            lines = f.readlines()

        with open(temp_filename, 'w') as f:
            f.writelines(unknown_typedefs)
            f.writelines(lines)

        translation_unit = index.parse(temp_filename, ['-x', 'c'])

    root_nodes = translation_unit.cursor.get_children()
    for node in root_nodes:
        if node.kind == CursorKind.FUNCTION_DECL:
            return Function(node)


def parse_func(filename, line_number):
    """
    Given a filename and a line number for a single function
    declaration/definition, attempts to parse it out into a Function object
    """
    # @@@TODO: this doesn't work on header files
    lines = [linecache.getline(filename, line_number - 1),
             linecache.getline(filename, line_number)]

    if "(" in lines[1]:
        i = 1
        while ")" not in lines[-1]:
            lines.append(linecache.getline(filename, line_number + i))
            i = i + 1

    lines.extend(";")

    with open("/tmp/hornbill_tmp.c", 'w') as f:
        f.writelines(lines)

    func = parse_temp_stubbed("/tmp/hornbill_tmp.c")

    return func


def compare(functions):
    """
    Compare functions parsed from C and functions parsed from docstrings
    """
    for f in functions:
        c = f[0]
        d = f[1]
        if c is None or d is None or not c == d:
            print("Mismatch between function and docstring")
            print("Function:")
            print(c)
            print("Docstring:")
            print(d)

            print("")
            print("")

def validate_c_file(filename):
    c_functions = parse_file_functions(filename)
    func_docstrings = find_func_docstrings(filename, c_functions, CommentFormat.Doxygen)

    compare(func_docstrings)

class BaseDocumentationError(object):
    base_string = "Error in function {funcname} at {filename}:{linenumber} - "
    string = "Base documentation error"

    def __init__(self, func, argname = None):
        self.func = func
        self.argname = argname

    def print_err(self):
        print(self.base_string.format(
                    funcname = self.func.name,
                    filename = self.func.location.filename,
                    linenumber = self.func.location.linenumber),
               end = "")

        if self.argname is not None:
            print(self.string.format(argname = self.argname))
        else:
            print(self.string)


class NoDocumentationError(BaseDocumentationError):
    string = "Is missing documentation!"

class MissingArgumentError(BaseDocumentationError):
    string = "Argument missing from docstring: {argname}"

class ExtraArgumentError(BaseDocumentationError):
    string = "Extra argument in docstring: {argname}"

class WrongArgumentError(BaseDocumentationError):
    string = "Argument incorrect in docstring: {argname}"

def find_documentation_errors(filename):
    c_functions = parse_file_functions(filename)
    func_docstrings = find_func_docstrings(filename, c_functions, CommentFormat.Doxygen)
    errors = list()

    for func in func_docstrings:
        c_def = func[0]
        doc   = func[1]

        if doc is None:
            errors.append(NoDocumentationError(c_def))
            continue

        if len(c_def.args) > len(doc.args):
            for arg in c_def.args:
                if arg not in doc.args:
                    errors.append(MissingArgumentError(c_def, arg.name))

        elif len(c_def.args) < len(doc.args):
            for arg in doc.args:
                if arg not in c_def.args:
                    errors.append(ExtraArgumentError(c_def, arg.name))

        else:
            for i in range(len(c_def.args)):
                if not c_def.args[i] == doc.args[i]:
                    errors.append(WrongArgumentError(c_def, c_def.args[i].name))


    return errors

if __name__ == "__main__":
    acceptable_types = {'edt', 'doxygen'}

    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check-comment',
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
    if args.check_comment:
        errors = find_documentation_errors(args.check_comment)
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
