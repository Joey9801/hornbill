def gen_doxygen(func):
    """
    Given a parsed function, generate a doxygen template
    Returns a string which contains C comment characters and newlines
    """

    lines = ["/**"]

    lines.append(" * {}".format(func.name))

    lines.append(" *")
    lines.append(" * {}".format(func.comment))


    for arg in func.args:
        lines.append(" *")
        lines.append(" * @param[{}] {} ({})".format(arg.inout, arg.name, arg.typename))
        lines.append(" *              {}".format(arg.comment))

    lines.append(" *")
    lines.append(" * @return {}".format(func.returns.typename))
    lines.append(" *              {}".format(func.returns.comment))
    lines.append(" */")


    return "\n".join(lines)
