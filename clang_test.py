#!python-venv/bin/python

from __future__ import print_function
import sys

import clang.cindex
from clang.cindex import CursorKind

def print_indent(indent_level):
    print(' '*indent_level, end="")

def print_node(node, indent_level):

    print_indent(indent_level)

    print("{} {}".format(node.kind, node.displayname))

    for c in node.get_children():
        print_node(c, indent_level + 1)

def print_function(func_node):
    print("Function: {}".format(func_node.canonical))
    print("  source_file  : {}".format(func_node.location.file))
    print("  source_line  : {}".format(func_node.location.line))
    print("  is_definition: {}".format(func_node.is_definition()))
    print("  is_static    : {}".format(func_node.is_static_method()))
    print("  return type  : {}".format(func_node.result_type.spelling))
    print("  Arguments    :")
    for i, arg in enumerate(func_node.get_arguments()):
        print("    Arg {}".format(i))
        print(dir(arg.type))
        print("      Type: \"{}\"".format(arg.type.spelling))
        print("      Name: \"{}\"".format(arg.spelling))

if __name__ == "__main__":
    clang.cindex.Config.set_library_file('/usr/lib/llvm-3.8/lib/libclang.so.1')
    index = clang.cindex.Index.create()

    translation_unit = index.parse(sys.argv[1], ['-x', 'c', '-fsyntax-only'])
    print(dir(translation_unit))

    for node in (x for x in translation_unit.cursor.get_children() if x.kind == CursorKind.FUNCTION_DECL):
        print(dir(node))
        print_function(node)
