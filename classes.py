import enum
from collections import namedtuple

from copy import deepcopy

Location = namedtuple("Location", ["filename", "linenumber"])


class CommentFormat(enum.Enum):
    Doxygen = 1
    EDT = 2


"""
Represents a comment as written in a C file.
"""
VerbatimComment = namedtuple("VerbatimComment",
                             ["start_loc", "end_loc", "comment"])


class Error(object):
    def __init__(self, linenumber = None, colnumber = None, error = ""):
        self.rel_linenumber = linenumber
        self.colnumber = colnumber
        self.error_msg = error
    def __str__(self):
        return "line: {}, col: {}\n{}".format(self.rel_linenumber, self.colnumber, self.error_msg)


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
            return "Type: {}, Name: {}, In/Out: {}".format(self.typename, self.name, self.inout)

    def __eq__(self, other):
        ret = True
        if self.name != other.name:
            ret = False
        if self.inout and other.inout:
            if self.inout != other.inout:
                ret = False
        if self.typename and other.typename:
            if self.typename != other.typename:
                ret = False
        return ret

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
            self.location = Location(filename=clang_node.location.file.name,
                                     linenumber=clang_node.location.line)
            self.name     = clang_node.spelling
            self.returns  = Variable(typename = clang_node.result_type.spelling,
                                     name     = "<return>")

            self.args     = [ Variable(typename = x.type.spelling,
                                       name     = x.spelling)
                              for x in clang_node.get_arguments() ]
        else:
            self.location = Location()
            self.name = None
            self.returns = None
            self.args = []

        self.comment = VerbatimComment(comment=["<Placeholder here>"],
                                       start_loc=-1,
                                       end_loc=-1)

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

    def __eq__(self, other):
        if not isinstance(other, Function):
            return False

        ret = True
        if self.location and other.location:
            if self.location != other.location:
                ret = False
        if self.name and other.name:
            if self.name != other.name:
                ret = False
        if self.returns and other.returns:
            if not self.returns == other.returns:
                ret = False
        if self.args and other.args:
            missing_args = deepcopy(other.args)
            for arg in self.args:
                found = False
                for barg in missing_args:
                    if arg == barg:
                        found = True
                        missing_args.remove(barg)
                        break
                if not found:
                    ret = False
        return ret

    def dictify(self):
        if self.location:
            loc = self.location._as_dict()
        else:
            loc = None

        return {"location": loc,
                "name"    : self.name,
                "returns" : self.returns.dictify(),
                "args"    : [x.dictify() for x in self.args],
                "comment" : self.comment}

class DummyFunction(Function):
    def __eq__(self, other):
        if isinstance(other, DummyFunction):
            return False
        elif isinstance(other, Function):
            return True


class ParserError():
    def __init__(self, problem, location=None):
        self.problem = problem
        self.location = location

    def __str__(self):
        string = str(self.problem)
        if self.location is not None:
            string += ": line " + str(self.location)

        return string
