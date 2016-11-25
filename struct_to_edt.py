#!/usr/bin/env python3

from __future__ import print_function

from collections import namedtuple


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


def test_edt():
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


if __name__ == '__main__':
    test_indent()
    test_edt()
    test_edt_to_comment()
    print('Tests passed.')
