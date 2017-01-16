from collections import namedtuple

Location = namedtuple("Location", ["filename", "linenumber"])

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
            self.location = Location(filename=clang_node.location.file.name,
                                     linenumber=clang_node.location.line)
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
        if self.location:
            loc = self.location._as_dict()
        else:
            loc = None

        return {"location": loc,
                "name"    : self.name,
                "returns" : self.returns.dictify(),
                "args"    : [x.dictify() for x in self.args],
                "comment" : self.comment}


