from Classes import *


def parse_edt(edt):
    """
    Parses an edt comment into a function class.    
    """
    f = Function()
    for i,line in enumerate(edt):
        if line.startswith(" * edt: "):
            f.name = line[8:].split()[2]
        elif line.startswith(" * Return: "):
            typename = line[11:].strip()
            f.returns = Variable(typename = typename, name = "<return>")
        elif line.startswith(" * Argument: "):
            arg = Variable()
            arg.name = line[13:].strip()
            next_line = edt[i+1][2:].strip().split()
            if next_line[0] == "IN:":
                arg.inout = "in"
            elif next_line[0] == "INOUT:":
                arg.inout = "inout"
            else:
                arg.inout = "out"
            arg.comment = next_line[-1]
            f.args.append(arg)

    return f


def check_edt(edt):
    """
    Checks an edt comment for errors.
    """
    errors = []
    stages = ["Fuction name", "Comment", "Return", "Args"]
    i = 0

    for j,line in enumerate(edt):
        if line.startswith(" * edt: ") and i == 0:
            # Found edt line
            i += 1
        if line.startswith(" * edt: ") and i != 0:
            error = Error(j, None, "Unexpected 'edt:' line")
            errors.append(error)
        elif line != " * " and i == 1:
            # Found the comment between edt line and return line
            i += 1
        elif line.startswith(" * Return: ") and i == 2:
            # Found return line
            i += 1
        elif line.startswith(" * Return: ") and i != 2:
            error = Error(j, None, "Unexpected 'Return:' line")
        elif line.startswith(" * Argument: "):
            continue





    return errors


        



_ref = """/*
 * edt: * function fry
 *
 * Fry some eggs.
 *
 * Return: cerrno
 *   Whether we fried the eggs. This line is very, very, very, very, very, very,
 *       very, very long.
 *
 * Argument: frying
 *   IN:     How many to fry.
 *
 * Argument: style
 *   INOUT:  Type of egg.
 */"""
_ref = _ref.split("\n")

if __name__ == "__main__":
    error = check_edt(_ref)
    if error:
        print(error)
    else:
        f = parse_edt(_ref)
        print(f)
