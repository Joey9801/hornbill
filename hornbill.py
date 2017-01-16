#!/home/ensoft/hornbill/venv/bin/python

import re
import sys
import json
import tempfile
import linecache

from classes import *

from edt import gen_edt
from doxygen import gen_doxygen, gen_doxygen_snippet
from formatter import format_func

import clang.cindex
from clang.cindex import CursorKind


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


if __name__ == "__main__":
    func = parse_func(sys.argv[2], int(sys.argv[3]))

    if sys.argv[1] == "edt":
        print(gen_edt(func))

    elif sys.argv[1] == "doxygen":
        gen_doxygen_snippet(func)

    elif sys.argv[1] == "format":
        print(format_func(func))

    elif sys.argv[1] == "debug":
        print(func)
