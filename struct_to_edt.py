#!python-venv/bin/python

from __future__ import print_function

from collections import namedtuple


def edt(func):
    """
    Creates an EDT from a function description object.

    The function description object should be as in common.py.
    Outputs a string, without its starting/ending /* and without stars
    down the side.
    """
    # First line is edt: * <category> <API-name>
    result = 'edt: * function '
    result += str(func.name)
    result += '\n\n'

    # Next line is a description
    result += func.comment + '\n\n'

    # Then the result, if present
    if func.returns:
        result += 'Return: ' + func.returns.type + '\n'
        result += '  ' + func.returns.comment + '\n'

    # Then we iterate through the argument:name pairs
    for arg in func.args:
        result += '\n'
        result += 'Argument: ' + arg.name + '\n'
        result += '  ' + arg.comment + '\n'

    return result

if __name__ == '__main__':
    print("Testing edt function...")

    func = namedtuple("Func", ['type', 'name', 'location',
                               'returns', 'comment', 'args'])
    arg = namedtuple("Arg", ['type', 'name', 'comment'])

    func.type = 'function'
    func.name = 'fry'
    func.location = {'file': 'egg.c', 'line': 100}
    func.comment = 'Fry some eggs.'
    arg1 = arg(type='int', name='frying',
               comment='How many to fry.')
    arg2 = arg(type='char*', name='style',
               comment='Type of egg.')
    func.args = [arg1, arg2]
    func.returns = arg(type='cerrno', comment='Whether we fried the eggs.',
                       name=None)

    reference = """edt: * function fry

Fry some eggs.

Return: cerrno
  Whether we fried the eggs.

Argument: frying
  How many to fry.

Argument: style
  Type of egg.
"""
    assert(edt(func) == reference)
    print('Testing passed.')
