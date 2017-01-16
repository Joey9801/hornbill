import os

def gen_doxygen(func):
    """
    Given a parsed function, generate a doxygen template
    Returns a string which contains C comment characters and newlines
    """

    lines = ["/**"]

    lines.append(" * ${0:" + func.name + "}")

    i = 1
    for arg in func.args:
        lines.append(" *")
        lines.append(" * @param[${" + str(i) + ":in}] " + arg.name)
        lines.append(" *              ${" + str(i+1) + ":" + arg.comment + "}")

        i += 2

    lines.append(" *")
    lines.append(" * @return ${" + str(i) + ":" + func.returns.typename + "}")
    lines.append(" *              ${" + str(i+1) + ":" + func.returns.comment + "}")
    lines.append(" */")


    return "\n".join(lines)

def gen_doxygen_snippet(func):
    body = gen_doxygen(func)

    snippet = "snippet qwerty12345\n" + body + "\nendsnippet"

    try:
        os.makedirs("/tmp/snippets")
    except OSError:
        pass

    with open("/tmp/snippets/c_hornbill.snippets", 'w') as f:
        f.write(snippet)
