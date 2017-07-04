from __future__ import print_function
import os

from classes import *
import c_parser
import comments


class BaseDocumentationError(object):
    base_string = "{filename}:{linenumber} in function {funcname} - "
    string = "Base documentation error"

    def __init__(self, func, argname = None):
        self.func = func
        self.argname = argname

    def print_err(self):
        print(self.base_string.format(
                    funcname = self.func.name,
                    filename = os.path.basename(self.func.location.filename),
                    linenumber = self.func.location.linenumber),
               end = "")

        if self.argname is not None:
            print(self.string.format(argname = self.argname))
        else:
            print(self.string)


class NoDocumentationError(BaseDocumentationError):
    string = "Is missing documentation!"


class NoReturnError(BaseDocumentationError):
    string = "Missing return documentation in non-void function"


class MissingArgumentError(BaseDocumentationError):
    string = "Argument missing from docstring: {argname}"


class ExtraArgumentError(BaseDocumentationError):
    string = "Extra argument in docstring: {argname}"


class WrongArgumentError(BaseDocumentationError):
    string = "Argument incorrect in docstring: {argname}"


def find_documentation_errors(filename):
    c_functions = c_parser.parse_file_functions(filename)
    func_docstrings = comments.find_func_docstrings(filename, c_functions)
    errors = list()

    for func in func_docstrings:
        c_def = func[0]
        doc   = func[1]

        if isinstance(doc, DummyFunction):
            continue

        elif doc is None:
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

        if c_def.returns.typename != "void" and doc.returns is None:
            errors.append(NoReturnError(c_def, None))

    return errors
