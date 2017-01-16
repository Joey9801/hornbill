import re

from classes import Function, Variable

def format_func(func, header = False):
    """
    Aligns the variables in a function definition as per ensoft coding
    standards
    """

    lines = []

    if header:
        lines.append(func.returns.typename + " " + func.name + "(")
    else:
        lines.append(func.returns.typename)
        lines.append(func.name + " (")

    var_start_col = len(lines[-1])

    if len(func.args) == 0:
        if header:
            lines[-1] += "void);"
        else:
            lines[-1] += "void)"

        return "\n".join(lines)

    max_type_len = 0
    max_num_asterisks = 0

    asterisks = re.compile("\*+$")

    for arg in func.args:
        m = asterisks.search(arg.typename)
        if m:
            max_num_asterisks = max(len(m.group(0)), max_num_asterisks)
            max_type_len = max(len(arg.typename) - len(m.group(0)) - 1, max_type_len)
        else:
            max_type_len = max(len(arg.typename), max_type_len)

    name_start_column = max_type_len + 1 + max_num_asterisks

    for arg in func.args:
        m = asterisks.search(arg.typename)
        if m:
            num_asterisks = len(m.group(0))
            typename = arg.typename[0:-num_asterisks-1]
        else:
            num_asterisks = 0
            typename = arg.typename

        lines[-1] += typename + " "*(name_start_column - len(typename) - num_asterisks) + "*"*num_asterisks + arg.name + ","
        lines.append(" "*var_start_col)

    lines = lines[0:-2]

    if header:
        lines[-1] = lines[-1][:-1] + ");"
    else:
        lines[-1] = lines[-1][:-1] + ")"

    for line in lines:
        print(line)

    return ""
