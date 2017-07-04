#!python-venv/bin/python

from __future__ import print_function

import re
import sys
import json
import tempfile
import linecache

from classes import *

import clang.cindex
from clang.cindex import CursorKind


"""
There are two possible approaches to getting all of the function definitions
out of the source file.

First:
    Could provide clang wit all the arguments necessary to actually compile
    the source file.

    Pros: Don't need to stub out the types
          Fewer places to go wrong
    Cons: Awkward configuration for XR
          Must write new config for each new project
          Could be slow for large TUs


Second:
    Could create a new stubbed version of the file and parse that. Remove the
    body of all the functions and replace with a single semicolon.

    Pros: Would be fast - not actually parsing any C code, only declarations
          No configuration per project, should just work
    Cons: More work to set up
          Higher change of systematically getting it wrong
          Have to work to preserve line numbers


This file implementes the second option.
"""

clang.cindex.Config.set_library_file('/usr/lib/llvm-3.8/lib/libclang.so.1')

def stub_lines(lines):
    """Remove any actual content from a set of lines describing c source, apart
    from the top level declarations of functions and structs."""
    #Remove the include
    for i, line in enumerate(lines):
        if line.startswith("#include"):
            lines[i] = "\n"

    # Remove all the function bodies. Or rather, replace all top level curly
    # braces with a single semicolon.
    # This removes the fields in any struct definitions, but that's OK for now.
    brace_levels = 0
    for i, line in enumerate(lines):
        line = list(line)
        for j, char in enumerate(line):
            if char == "{":
                if brace_levels == 0:
                    line[j] = ";"
                else:
                    line[j] = " "

                brace_levels += 1

            elif char == "}":
                if brace_levels > 0:
                    line[j] = " "

                brace_levels -= 1

            elif brace_levels > 0 and char != "\n":
                line[j] = " "

        line = "".join(line)

        if line.startswith("typedef"):
            line = "// " + line

        lines[i] = line

    return lines

def create_stubbed_file(filename):
    """Transforms a single C source file into a new source file, but with each
    function definition replaced with a similar declaration

    Returns the filename of the new file
    """

    stubbed_filename = "/tmp/hornbill_tmp.c"

    with open(filename, 'r') as f:
        lines = f.readlines()

    #Remove all includes and function bodies
    lines = stub_lines(lines)

    with open(stubbed_filename, 'w') as f:
        f.writelines(lines)

    root_nodes, unknown_types = clang_parse_file(stubbed_filename)

    typedefs = "".join(["typedef int {};".format(x) for x in unknown_types])

    with open(stubbed_filename, 'w') as f:
        f.writelines([typedefs])
        f.writelines(lines)

    return stubbed_filename


def clang_parse_file(filename):
    """Parses a C source file into an AST with clang.
    Returns (list(ast root nodes), list(unknown types))
    """

    index = clang.cindex.Index.create()

    translation_unit = index.parse(filename, ['-x', 'c'])

    unknown_types = []
    for d in translation_unit.diagnostics:
        if d.severity == 3:
            quoted = re.compile("'([^']*)'")
            for value in quoted.findall(d.spelling):
                unknown_types.append(value)

    root_nodes = translation_unit.cursor.get_children()

    return (root_nodes, unknown_types)


def parse_file_functions(filename):
    """Returns a list of parsed Function objects from a given C file"""
    clang.cindex.Config.set_library_file('/usr/lib/llvm-3.8/lib/libclang.so.1')

    stubbed_filename = create_stubbed_file(filename)

    root_nodes, _ = clang_parse_file(stubbed_filename)

    functions = [Function(x) for x in root_nodes if x.kind == CursorKind.FUNCTION_DECL]

    for f in functions:
        f.location.filename = filename

    return functions
