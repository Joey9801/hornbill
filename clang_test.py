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

if __name__ == "__main__":
    clang.cindex.Config.set_library_file('/usr/lib/llvm-3.8/lib/libclang.so.1')
    index = clang.cindex.Index.create()

    translation_unit = index.parse(sys.argv[1], ['-x', 'c'])
    print(dir(translation_unit))

    for node in (x for x in translation_unit.cursor.get_children() if x.kind == CursorKind.FUNCTION_DECL):
        print(dir(node))
        print_node(node, 0)
