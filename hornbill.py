#!python-venv/bin/python

import sys
import json
import linecache
import tempfile

import clang.cindex
from clang.cindex import CursorKind

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
    def __init__(self, typename = "", name = "", comment = ""):
        self.typename = typename
        self.name     = name
        self.comment  = comment

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
            self.name     = clang_node.displayname
            self.name     = self.name[0:self.name.find("(")]
            self.returns  = Variable(typename = clang_node.result_type.spelling,
                                     name     = "<return>")
            self.args     = [ Variable(typename = x.type.spelling,
                                       name     = x.spelling)
                              for x in clang_node.get_arguments() ]

            self.comment  = clang_node.raw_comment

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

    print(temp_filename)

    with open(temp_filename) as f:
        print(f.readlines())

    clang.cindex.Config.set_library_file('/usr/lib/llvm-3.8/lib/libclang.so.1')
    index = clang.cindex.Index.create()

    translation_unit = index.parse(temp_filename, ['-x', 'c', '-fsyntax-only'])
    root_nodes = translation_unit.cursor.get_children()

    for x in root_nodes:
        print(x)
        if x.kind == CursorKind.FUNCTION_DECL:
            return Function(x)

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
            lines.extend(linecache.getline(filename, line_number + 1))

    lines.extend(";")

    print(lines)
    with open("/tmp/hornbill_tmp.c", 'w') as f:
        f.writelines(lines)

    func = parse_temp_stubbed("/tmp/hornbill_tmp.c")

    return func

if __name__ == "__main__":
    func = parse_func(sys.argv[1], int(sys.argv[2]))

    print(func)
