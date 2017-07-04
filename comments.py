from classes import *

from edt import parse_edt
from doxygen import parse_doxygen


class _State(enum.Enum):
    """
    During parsing, we need to keep track of which kind of comment line
    we are currently on.
    """
    COMMENT_STARTED = 4
    COMMENT_ENDED = 5
    COMMENT_NOT_ENCOUNTERED = 6


def _find_toplevel_comments(c_lines, comment_format, filename=None):
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
            comment = [comment_start]
        elif line == ' */' and state == _State.COMMENT_STARTED:
            state = _State.COMMENT_ENDED
            comment.append(' */')

            comments.append(VerbatimComment(comment=comment,
                                            start_loc=start_line,
                                            end_loc=num+1,
                                            filename=filename))
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

    return _find_toplevel_comments(c_lines, comment_format, filename)


def find_func_docstrings(filename, functions):
    """
    For each function in the given list of functions, attempts to find the
    relevant docstring in filename.
    Returns a zipped object of (function, relevant_docstring), where
    relevant_docstring is None if no suitable comment could be found
    """

    doxygen_comments = find_toplevel_docstrings(filename, CommentFormat.Doxygen)
    edt_comments = find_toplevel_docstrings(filename, CommentFormat.EDT)

    found_docstrings = list()

    # Match all the doxygen comments first.
    for func in functions:
        func_line = func.location.linenumber

        found = False
        for docstring in doxygen_comments:
            if func_line - 2 <= docstring.end_loc < func_line:
                found_docstrings.append(parse_doxygen(docstring))
                found = True
                break

        if not found:
            found_docstrings.append(None)

    if None not in found_docstrings:
        return zip(functions, found_docstrings)
    else:
        for i, verbatim_comment in enumerate(edt_comments):
            try:
                edt_comments[i] = parse_edt(verbatim_comment)
            except ParserError as e:
                edt_comments[i] = None
                print(e)


    # Then try to find an EDT comment for any remaining. Most EDT's are linked
    # to their function by name, but some (eg: ones which say "EDT in blah.h")
    # must be matched positionally.
    for func, docstring, i in zip(functions, found_docstrings, range(len(functions))):
        if docstring is not None:
            continue

        func_line = func.location.linenumber

        for edt in edt_comments:
            if edt is not None:
                if func.name == edt.name:
                    found_docstrings[i] = edt
                    break

                if func_line - 2 <= edt.docstring.end_loc < func_line:
                    found_docstrings[i] = edt
                    break

    return zip(functions, found_docstrings)
