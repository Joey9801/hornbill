from classes import *


def parse_edt(edt):
    """
    Parses an edt comment into a function class.    
    """
    f = Function()
    for i,line in enumerate(edt.comment):
        print(line)
        if line.startswith(" * edt: "):
            f.name = line[8:].split()[2]
        elif line.startswith(" * Return: "):
            typename = line[11:].strip()
            f.returns = Variable(typename = typename, name = "<return>")
        elif line.startswith(" * Argument: "):
            arg = Variable()
            arg.name = line[13:].strip()
            next_line = edt.comment[i+1][2:].strip().split()
            import code; code.interact(local=locals())
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

    We use an index, i, to keep track of the part of the edt we're expecting
    next. The stages are ['edt', 'comment', 'return', 'arguments']
    """
    errors = []
    i = 0
    for j,line in enumerate(edt):
        if line.startswith(" * edt: ") and i == 0:
            # Found edt line
            i = 1
        elif line.startswith(" * edt: ") and i != 0:
            error = Error(j, None, "Unexpected 'edt:' line")
            errors.append(error)
        elif line.startswith(" * Return: ") and i == 2:
            # Found return line
            i = 3
        elif line.startswith(" * Return: ") and i != 2:
            if i == 0:
                error = Error(j, None, "Missing 'edt:' line.")
            elif i == 1:
                error = Error(j, None, "Missing function comment.")
            else:
                error = Error(j, None, "Unexpected 'Return:' line.")
            errors.append(error)
        elif line.startswith(" * Argument: ") and i == 2:
            error = Error(j, None, "Missing 'Return:' line.")
            errors.append(error)
            i = 3 # So we don't repeat the error.
        elif line.strip() != "*" and i == 1:
            # Found the comment between edt line and return line
            print "Found comment!"
            print [line]
            i = 2

    return errors



_ref = """/*
 * edt: * function fry
 *
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
    errors = check_edt(_ref)
    if errors:
        print "Errors found in edt"
        for e in errors:
            print e
    else:
        print "No errors found in edt."
        f = parse_edt(_ref)
        print(f)
