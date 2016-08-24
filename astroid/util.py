# Copyright (c) 2015-2016 Cara Vinson <ceridwenv@gmail.com>
# Copyright (c) 2015-2016 Claudiu Popa <pcmanticore@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER

import importlib
import platform
import sys
import warnings

import lazy_object_proxy
import six
import wrapt

JYTHON = platform.python_implementation() == 'Jython'

try:
    from functools import singledispatch as _singledispatch
except ImportError:
    from singledispatch import singledispatch as _singledispatch


def singledispatch(func):
    old_generic_func = _singledispatch(func)
    @wrapt.decorator
    def wrapper(func, instance, args, kws):
        return old_generic_func.dispatch(type(args[0]))(*args, **kws)
    new_generic_func = wrapper(func)
    new_generic_func.register = old_generic_func.register
    new_generic_func.dispatch = old_generic_func.dispatch
    new_generic_func.registry = old_generic_func.registry
    new_generic_func._clear_cache = old_generic_func._clear_cache
    return new_generic_func


def lazy_descriptor(obj):
    class DescriptorProxy(lazy_object_proxy.Proxy):
        def __get__(self, instance, owner=None):
            return self.__class__.__get__(self, instance)
    return DescriptorProxy(obj)


def lazy_import(module_name):
    return lazy_object_proxy.Proxy(
        lambda: importlib.import_module('.' + module_name, 'astroid'))

def reraise(exception):
    '''Reraises an exception with the traceback from the current exception
    block.'''
    six.reraise(type(exception), exception, sys.exc_info()[2])

def generate_warning(message, warning):
    return lambda strings: warnings.warn(message % strings, warning,
                                         stacklevel=3)

rename_warning = generate_warning("%r is deprecated and slated for removal in "
                                  "astroid 2.0, use %r instead",
                                  PendingDeprecationWarning)

attr_to_method_warning = generate_warning("%s is deprecated and slated for "
                                          " removal in astroid 1.6, use the "
                                          "method '%s' instead.",
                                          PendingDeprecationWarning)

@object.__new__
class Uninferable(object):
    """Special inference object, which is returned when inference fails."""
    def __repr__(self):
        return 'Uninferable'
    __str__ = __repr__

    def __getattribute__(self, name):
        if name == 'next':
            raise AttributeError('next method should not be called')
        if name.startswith('__') and name.endswith('__'):
            return object.__getattribute__(self, name)
        if name == 'accept':
            return object.__getattribute__(self, name)
        return self

    def __call__(self, *args, **kwargs):
        return self

    def __bool__(self):
        return False

    __nonzero__ = __bool__

    def accept(self, visitor):
        func = getattr(visitor, "visit_uninferable")
        return func(self)

class BadOperationMessage(object):
    """Object which describes a TypeError occurred somewhere in the inference chain

    This is not an exception, but a container object which holds the types and
    the error which occurred.
    """


class BadUnaryOperationMessage(BadOperationMessage):
    """Object which describes operational failures on UnaryOps."""

    def __init__(self, operand, op, error):
        self.operand = operand
        self.op = op
        self.error = error

    def __str__(self):
        operand_type = self.operand.name
        msg = "bad operand type for unary {}: {}"
        return msg.format(self.op, operand_type)


class BadBinaryOperationMessage(BadOperationMessage):
    """Object which describes type errors for BinOps."""

    def __init__(self, left_type, op, right_type):
        self.left_type = left_type
        self.right_type = right_type
        self.op = op

    def __str__(self):
        msg = "unsupported operand type(s) for {}: {!r} and {!r}"
        return msg.format(self.op, self.left_type.name, self.right_type.name)


def _instancecheck(cls, other):
    wrapped = cls.__wrapped__
    other_cls = other.__class__
    is_instance_of = wrapped is other_cls or issubclass(other_cls, wrapped)
    rename_warning((cls.__class__.__name__, wrapped.__name__))
    return is_instance_of


def proxy_alias(alias_name, node_type):
    """Get a Proxy from the given name to the given node type."""
    proxy = type(alias_name, (lazy_object_proxy.Proxy,),
                 {'__class__': object.__dict__['__class__'],
                  '__instancecheck__': _instancecheck})
    return proxy(lambda: node_type)


# Backwards-compatibility aliases
YES = Uninferable

def register_implementation(base):
    """Register an implementation for the given *base*

    The given base class is expected to have a `register` method,
    similar to what `abc.ABCMeta` provides when used.
    """
    def wrapped(impl):
        base.register(impl)
        return impl
    return wrapped
