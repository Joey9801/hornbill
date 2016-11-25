#!/home/joe/Documents/independence_day/hornbill/python-venv/bin/python

import re
import sys
import json
import tempfile
import linecache

from edt import gen_edt
from doxygen import gen_doxygen

import clang.cindex
from clang.cindex import CursorKind

import struct_to_edt


class Location(object):
    def __init__(self, filename = "", linenumber = ""):
        self.filename   = filename
        self.linenumber = linenumber

    def __str__(self):
        return "{}:{}".format(self.filename, self.linenumber)

    def dictify(self):
        return {"filename": self.filename,
                "line"    : self.linenumber}


class Variable(object):
    def __init__(self, typename = "", name = "", comment = "<Placeholder comment>"):
        self.typename = typename
        self.name     = name
        self.comment  = comment
        self.inout    = "in"

    def __str__(self):
        if self.name == "<return>":
            return "{}".format(self.typename)
        else:
            return "Type: {}, Name: {}".format(self.typename, self.name)

    def dictify(self):
        if self.name == "<return>":
            return {"type"   : self.typename,
                    "comment": self.comment}

        else:
            return {"name"   : self.name,
                    "type"   : self.typename,
                    "comment": self.comment}


class Function(object):
    def __init__(self, clang_node = None):
        if clang_node is not None:
            self.location = Location(clang_node.location.file.name,
                                     clang_node.location.line)
            self.name     = clang_node.spelling
            self.returns  = Variable(typename = clang_node.result_type.spelling,
                                     name     = "<return>")

            self.args     = [ Variable(typename = x.type.spelling,
                                       name     = x.spelling)
                              for x in clang_node.get_arguments() ]

            self.comment  = "<Placeholder comment>"

    def __str__(self):
        string = ""
        string += "Function {}\n".format(self.name)
        string += "  Location: {}\n".format(self.location)
        string += "  Returns : {}\n".format(self.returns)
        if self.args:
            string += "  Args:\n"
            for arg in self.args:
                string += "    {}\n".format(arg)

        return string

    def dictify(self):
        return {"location": self.location.dictify(),
                "name"    : self.name,
                "returns" : self.returns.dictify(),
                "args"    : [x.dictify() for x in self.args],
                "comment" : self.comment}


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
        print(gen_doxygen(func))
