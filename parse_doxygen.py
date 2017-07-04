from __future__ import print_function

import os
import enum
import re

from classes import Function, DummyFunction, Variable, CommentFormat, VerbatimComment

from edt_to_func import parse_edt


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
    words = line.strip().split()

    if len(words) < 2:
        return ""
    else:
        return words[1]

def _is_reference(lines):
    """
    Returns True iff the comment lines seem to indicate that the documentation
    can be found elsewhere.
    """

    key_phrases = [
            "function description",
            "for documentation",
            "see"
            ]

    header_file = re.compile(".* [^. ]*\.h.*")
    implements_cb = re.compile(".* (implements) [^ ]*_cb.*")

    # Referencing a header file?
    for line in lines:
        if header_file.match(line):
            for phrase in key_phrases:
                if phrase in line.lower():
                    return True

    # Referencing a callback type?
    for line in lines:
        if implements_cb.match(line):
            return True

    return False


def parse_doxygen(in_lines):
    """
    Parse lines representing a Doxygen comment into a structure.

    The lines may be a list of lines, or a VerbatimComment.

    The list of lines should be verbatim plucked from a C file.
    The result is a Function object.
    """
    if isinstance(in_lines, VerbatimComment):
        internal_lines = in_lines.comment
    else:
        internal_lines = in_lines

    lines = [line.strip() for line in internal_lines]

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

    if _is_reference(lines):
        return DummyFunction()

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
        result.returns = Variable(name="<return>")
    else:
        result.returns = None

    result.args = [Variable(name=arg) for arg in params]
    result.location = None
    result.name = None
    result.comment = '\n'.join(initial_comment).strip()

    return result



def _find_toplevel_comments(c_lines, comment_format):
    """
    Find all top-level Doxygen docstrings in a C file.

    Returns a list of VerbatimComments.

    c_lines is a list of lines of C source.
    """
    comments = []  # This is what we will return
    c_lines = [l.rstrip() for l in c_lines]
    state = _State.COMMENT_NOT_ENCOUNTERED

    if comment_format == CommentFormat.Doxygen:
        comment_start = "/**"
    elif comment_format == CommentFormat.EDT:
        comment_start = "/*"
    else:
        raise InputError("Unknown CommentFormat {}".format(comment_format))

    for num, line in enumerate(c_lines):
        if line == comment_start:
            state = _State.COMMENT_STARTED
            start_line = num + 1
            comment = ['/**']
            current_comment = VerbatimComment(comment=['/**'],
                                              start_loc=num+1,
                                              end_loc=-1)
        elif line == ' */' and state == _State.COMMENT_STARTED:
            state = _State.COMMENT_ENDED
            comment.append(' */')

            comments.append(VerbatimComment(comment=comment,
                                            start_loc=start_line,
                                            end_loc=num+1))
        else:
            if state == _State.COMMENT_STARTED:
                comment.append(line)

    return comments


def find_toplevel_docstrings(filename, comment_format):
    """
    Find all top-level docstrings in a C file.

    Returns a list of the function docstrings, each docstring a VerbatimComment.

    c_lines is a list of lines of C source.
    comment_format is a CommentFormat enum.
    """

    with open(filename) as f:
        c_lines = f.readlines()

    return _find_toplevel_comments(c_lines, comment_format)


def find_func_docstrings(filename, functions, comment_format):
    top_level_docstrings = find_toplevel_docstrings(filename, comment_format)

    found_docstrings = list()

    for func in functions:
        func_line = func.location.linenumber

        matching_docstring = None
        for docstring in top_level_docstrings:
            if func_line - 2 <= docstring.end_loc < func_line:
                matching_docstring = docstring
                break

        if matching_docstring is not None:
            if comment_format == CommentFormat.Doxygen:
                found_docstrings.append(parse_doxygen(matching_docstring))
            elif comment_format == CommentFormat.EDT:
                found_docstrings.append(parse_edt(matching_docstring))
        else:
            found_docstrings.append(None)

    return zip(functions, found_docstrings)

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

    expected = [Function()]
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
