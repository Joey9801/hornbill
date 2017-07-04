#!/usr/bin/env python3

from __future__ import print_function

from collections import namedtuple
import enum
import re

from classes import *

_location = None

def wrap_single_line(line, length=80, indent_len=4, already_indented=False):
    """
    Take a string and, if it is too long, convert it to several smaller.

    Given a string which is shorter than or equal to the length, returns
    [str].
    Given a string which is too long, returns [str1, str2, ...], where
    str1 + str2 + ... is equal to str except that spacing may be different,
    and where str1, str2, ... all have indentation equal to str's indentation
    plus the indentation width.
    already_indented tracks the negation of whether we need to indent again.
    """
    if len(line) <= length:
        return [line]

    # Slice the line if it's too long, based on the previous whitespace
    if line[length-1].isspace():
        before_whitespace = line[:length-1].rsplit(' ', 1)[0]
        if before_whitespace.isspace():
            # If we're only typing spaces, there's no point trying to break at a
            # sane place, so just break at the end
            last_whitespace = length
        else:
            last_whitespace = len(before_whitespace)
    else:
        last_whitespace = length

    # We can be sure that up to last_whitespace should definitely be on the
    # first line.
    result = [line[:last_whitespace]]

    # To wrap the remaining string, we should indent on the front
    current_indent = len(line) - len(line.lstrip())
    remaining = (' ' * current_indent) + line[last_whitespace:].lstrip()

    if not already_indented:
        remaining = (' ' * indent_len) + remaining

    rest_of_lines = wrap_single_line(line=remaining,
                                     length=length,
                                     indent_len=indent_len,
                                     already_indented=True)
    return result + rest_of_lines


def edt_to_comment(in_str, length=80):
    """
    Convert an EDT string to a fully-formed C comment, wrapped at end of line.

    Wraps so that every line is fewer than `length` characters long.
    Takes a string and puts comment marks on either side, and puts * down the
    left-hand side.
    """
    # For each line, wrap it at length-3, to make room for ' * ' at the start
    lines = [wrap_single_line(line, length-3) for line in in_str.split('\n')]
    # Flatten into a single list of lines
    lines = [line for linelist in lines for line in linelist]

    # Add comment marks
    # If a line is nonempty, we want it to start with ' * ';
    # otherwise we want it to start with [and be] ' *'.
    # int(bool(.)) takes the integer and outputs 0 if it's 0, and 1 otherwise.
    lines = [' *' + ' '* int(bool(len(line))) + line for line in lines]
    lines = ['/*'] + lines

    result_str = '\n'.join(lines)
    # Add the closing comment mark, which means replacing the final space 
    # with a slash
    # Python has immutable strings which is here annoying
    result_list = list(result_str)
    result_list[-1] = '*/'
    result_str = ''.join(result_list)

    return result_str


def edt_func(func, edt='edt'):
    """
    Creates an EDT from a function description object.

    The function description object should be as in common.py.
    Outputs a string, without its starting/ending /* and without stars
    down the side.

    Supply edt='<other thing>' to use something other than 'edt' on the first
    line of the EDT.
    """
    COMMENT_TEMPLATE = '<Description>'

    # First line is edt: * <category> <API-name>
    result = edt + ': * function '
    result += str(func.name)
    result += '\n\n'

    # Next line is a description
    if func.comment is None:
        result += COMMENT_TEMPLATE + '\n\n'
    else:
        result += func.comment + '\n\n'

    # Then the result, if present
    if func.returns:
        result += 'Return: ' + func.returns.typename + '\n'
        result += '  ' + func.returns.comment + '\n'

    # Then we iterate through the argument:name pairs
    for arg in func.args:
        result += '\n'
        result += 'Argument: ' + arg.name + '\n'
        if arg.inout:
            result += '  ' + arg.inout.upper() + ':'
            # Align the Argument part with the variable on the line above
            result += ' ' * (len('Argument') - len(arg.inout) - 3)
        result += '  ' + arg.comment + '\n'

    return result


class _State(enum.Enum):
    """Parsing state machine states"""
    INITIAL_COMMENT = 1
    PARAM = 2
    RETURN = 3

def _parse_edt_defition_line(line):
    assert(line.startswith("edt:"))

    global _location

    line = line[len("edt:"):].strip()
    parts = line.split()

    if len(parts) != 3:
        raise ParserError("EDT definition line \"{}\" appears malformed".format(line),
                _location)

    for i, part in enumerate(parts):
        if part == "*":
            parts[i] = None

    return parts

def _get_varname(line):
    assert(line.startswith("Argument:"))

    global _location

    parts = line.split()

    if len(parts) != 2 and len(parts) != 3:
        raise ParserError("EDT 'Argument' line \"{}\" appears malformed".format(line),
                _location)

    return parts[-1]


def _is_reference(lines):
    """
    Returns True iff the comment lines seem to indicate that the documentation
    can be found elsewhere.
    """

    key_phrases = [
            "function description",
            "for documentation",
            "see",
            "edt in"
            ]

    header_file = re.compile(".* [^. ]*\.h.*")
    implements_cb = re.compile(".*implements [^ ]*((_cb)|(_fn)|(_func)).*")

    # Referencing a header file?
    for line in lines:
        if header_file.match(line):
            for phrase in key_phrases:
                if phrase in line.lower():
                    return True

    # Referencing a callback type?
    for line in lines:
        if implements_cb.match(line.lower()):
            return True

    return False


def parse_edt(in_lines):
    """
    Parses an edt comment into a function class.
    """

    global _location

    if isinstance(in_lines, VerbatimComment):
        lines = in_lines.comment
        _location = in_lines.start_loc
    else:
        lines = in_lines
        _location = None

    lines = [line.strip() for line in lines]

    if lines[0] != "/*":
        raise ParserError("First line {} is not /*.".format(lines[0]),
                _location)

    for i, line in enumerate(lines[1:]):
        if _location != None:
            _location += 1
        if line[0] != '*':
            raise ParserError("Comment line does not start with *",
                _location)

    if lines[-1] != "*/":
        if _location != None:
            _location += 1
        raise ParserError("Last line is not */.", _location)

    lines = [x[1:].strip() for x in lines[1:-1]]
    if _location != None:
        _location -= len(lines)

    # At this point, 'lines' is a list of the lines of text which make up the
    # comment, exlucing all leading '/*', '*', and '*/' tokens.

    # The first line should always be the definition line, of the form:
    #  "edt: * * func_name"
    # Where the asterisks may be some other token

    params = list()
    returns = list()
    initial_comment = list()
    def_line = None

    which_state = _State.INITIAL_COMMENT
    for line in lines:
        if _location != None:
            _location += 1

        if line.startswith("edt:"):
            if def_line is not None:
                for line in lines:
                    print(line)
                raise ParserError("Multiple EDT definition lines found!",
                        _location)

            def_line = _parse_edt_defition_line(line)

        elif line.startswith("Argument:"):
            which_state = _State.PARAM
            params.append(_get_varname(line))

        elif line.startswith("Return:"):
            which_state = _State.RETURN
            returns.append(line)

        else:
            if which_state == _State.INITIAL_COMMENT:
                initial_comment.append(line)


    if _is_reference(initial_comment):
        result = DummyFunction()
        if def_line is not None:
            result.name = def_line[2]

    elif def_line is None:
        return None
    else:
        result = Function()
        if returns:
            result.returns = Variable(name="<return>")
        else:
            result.returns = None

        result.args = [Variable(name=arg) for arg in params]
        result.location = None
        result.name = def_line[2]
        result.comment = "\n".join(initial_comment).strip()

    if isinstance(in_lines, VerbatimComment):
        result.docstring = in_lines
    else:
        result.docstring = None

    return result

def gen_edt(func):
    return edt_to_comment(edt_func(func))


def test_indent():
    """
    Test the Indentation features.
    """
    assert(wrap_single_line('abc') == ['abc'])
    wrapped = wrap_single_line('abcdef',
                               length=4,
                               indent_len=1)
    assert(wrapped == ['abcd', ' ef'])

    wrapped = wrap_single_line('abcdef',
                               length=4,
                               indent_len=1,
                               already_indented=True)
    assert(wrapped == ['abcd', 'ef'])

    wrapped = wrap_single_line('abcdefghijk',
                               length=4,
                               indent_len=2)
    assert(wrapped == ['abcd', '  ef', '  gh', '  ij', '  k'])


_reference_edt = """edt: * function fry

Fry some eggs.

Return: cerrno
  Whether we fried the eggs. This line is very, very, very, very, very, very, very, very long.

Argument: frying
  IN:     How many to fry.

Argument: style
  INOUT:  Type of egg.
"""

_reference_comment = """/*
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


def test_edt_creator():
    """
    Test the EDT creator.
    """
    func = namedtuple("Func", ['type', 'name', 'location',
                               'returns', 'comment', 'args'])
    arg = namedtuple("Arg", ['typename', 'name', 'comment', 'inout'])

    func.type = 'function'
    func.name = 'fry'
    func.location = {'file': 'egg.c', 'line': 100}
    func.comment = 'Fry some eggs.'
    arg1 = arg(typename='int', name='frying',
               comment='How many to fry.',
               inout='IN')
    arg2 = arg(typename='char*', name='style',
               comment='Type of egg.',
               inout='INOUT')
    func.args = [arg1, arg2]
    func.returns = arg(typename='cerrno',
                       comment='Whether we fried the eggs. This line is very, '\
                               'very, very, very, very, very, very, very long.',
                       name=None, inout=None)

    assert(edt_func(func) == _reference_edt)


def test_edt_to_comment():
    """
    Test the edt_to_comment function.
    """
    assert(edt_to_comment(_reference_edt) == _reference_comment)


def gen_edt(func):
    return edt_to_comment(edt_func(func))


if __name__ == '__main__':
    test_indent()
    test_edt()
    test_edt_to_comment()
    print('Tests passed.')
