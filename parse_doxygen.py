#!/usr/bin/env python3

from __future__ import print_function

import os
import enum

from copy import deepcopy

from classes import Function
from classes import Variable
from classes import CommentFormat

class _State(enum.Enum):
    """
    During parsing, we need to keep track of which kind of comment line
    we are currently on.
    """
    INITIAL_COMMENT = 1
    RETURN = 2
    PARAM = 3
    COMMENT_STARTED = 4
    COMMENT_ENDED = 5
    COMMENT_NOT_ENCOUNTERED = 6


def _get_varname(line):
    """
    Given a single line of comment, return the variable name it is commenting.
    """
    return line.strip().split()[-1]


def parse_doxygen(in_lines):
    """
    Parse a list of lines representing a Doxygen comment into a structure.

    The list of lines should be verbatim plucked from a C file.
    The result is a Function object.
    """
    lines = [line.strip() for line in in_lines]

    if lines[0] != "/**":
        raise AssertionError("First line {} is not /**.".format(in_lines[0]))

    lines = lines[1:]
    for i, line in enumerate(lines):
        if line[0] != '*':
            raise AssertionError("Line {} does not start with a *.".format(i+2))

    lines = [line[1:].strip() for line in lines]

    # lines have had comments stripped from them
    if line[-1] != '/':
        raise AssertionError("Last line {} is not */".format(in_lines[-1]))

    lines = lines[:-1]

    # Split the lines list; its format is "overall comment", then a list of
    # parameters/return values, each with a comment.
    params = []
    returns = []
    initial_comment = []

    which_state = _State.INITIAL_COMMENT
    for line in lines:
        if line.startswith("@param"):
            which_state = _State.PARAM
            params.append(_get_varname(line))
        elif line.startswith("@return"):
            which_state = _State.RETURN
            returns.append(line)
        else:
            # It's a comment; skip
            if which_state == _State.INITIAL_COMMENT:
                initial_comment.append(line)

    if len(returns) > 1:
        raise AssertionError("Found more than one return: {}".format(returns))

    result = Function()

    if returns:
        print("Returns")

        result.returns = Variable(name="<return>")
    else:
        result.returns = None

    result.args = [Variable(name=_get_varname(arg)) for arg in params]
    result.location = None
    result.name = None
    result.comment = '\n'.join(initial_comment).strip()

    return result


def _find_toplevel_doxygen(c_lines):
    """
    Find all top-level Doxygen docstrings in a C file.

    Returns a list of the function docstrings, each docstring split on its
    newlines. (For example, [['/**', ' *', ' * things', ' */']].)

    c_lines is a list of lines of C source.
    """
    comments = []  # This is what we will return
    c_lines = [l.rstrip() for l in c_lines]
    state = _State.COMMENT_NOT_ENCOUNTERED

    for line in c_lines:
        if line == '/**':
            state = _State.COMMENT_STARTED
            current_comment = ['/**']
        elif line == ' */' and state == _State.COMMENT_STARTED:
            state = _State.COMMENT_ENDED
            current_comment.append(' */')
            comments.append(deepcopy(current_comment))
        else:
            if state == _State.COMMENT_STARTED:
                current_comment.append(line)

    return comments


def find_toplevel_docstrings(c_lines, comment_format):
    """
    Find all top-level docstrings in a C file.

    Returns a list of the function docstrings, each docstring split on its
    newlines. (For example, [['/**', ' *', ' * things', ' */']].)

    c_lines is a list of lines of C source.
    comment_format is a CommentFormat enum.
    """
    if comment_format == CommentFormat.Doxygen:
        return _find_toplevel_doxygen(c_lines)
    elif comment_format == CommentFormat.EDT:
        return _find_toplevel_edt(c_lines)
    else:
        raise InputError("Unknown CommentFormat {}".format(comment_format))


def _test_parser():
    lines = ["/**",
             " * Gets the node status from an instance derived from Base:Node",
             " *",
             " * @param[in] clips_env",
             " *              Clips environment pointer",
             " *",
             " * @param[in] inst_ptr",
             " *              A generic pointer to the data node instance",
             " *",
             " * @param[out] status",
             " *              Enumeration of the possible node status's",
             " *",
             " * @return SUCCESS or",
             " *         INVALID_ARG (if instance passed is not a ...",
             " */"
             ]
    ans = parse_doxygen(lines).dictify()
    print(ans)
    print('----')


def _test_docstring_finder():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dir_path, 'test_sources', 'confidential.c')) as f:
        lines = f.readlines()

    docstrings = find_toplevel_docstrings(lines, CommentFormat.Doxygen)

    for l in docstrings:
        print(parse_doxygen(l))



if __name__ == '__main__':
    _test_parser()
    _test_docstring_finder()
