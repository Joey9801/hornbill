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
        if c != d:
            print("Mismatch between function and docstring")
            print("Function:")
            print(c)
            print("Docstring:")
            print(d)

            print("")
            print("")

def foobar(filename):
    c_functions = parse_file_functions(filename)
    func_docstrings = find_func_docstrings(filename, c_functions, CommentFormat.Doxygen)

    compare(func_docstrings)

if __name__ == "__main__":
    acceptable_types = {'edt', 'doxygen'}

    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('check-comment',
                        help='Validate docstrings and declarations in a C file')
    mode.add_argument('type',
                      help='edt or doxygen',
                      choices=acceptable_types)
    mode.add_argument('--format',
                      action='store_true',
                      help='Format the function nicely.')

    parser.add_argument('file', help='C file to examine')
    parser.add_argument('line', help='Line number of function name', type=int)
    parser.add_argument('debug',
                        help='Turn on debug mode',
                        action='store_true')


    args = parser.parse_args()
    if args.check_comment:
        foobar(args.check_comment)
        exit()

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
