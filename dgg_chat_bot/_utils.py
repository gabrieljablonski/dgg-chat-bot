from sys import maxsize
from typing import Callable, Type, Union, _Final
from inspect import cleandoc, signature
from functools import wraps


def sanitize_docs(docs):
    return cleandoc(docs).replace('\n', ' ')


def enclose(strings, char):
    return [f"{char}{s}{char}" for s in strings]


def parametrized_decorator_method(decorator):
    """
    Meta decorator for cleanly creating decorators that accept parameters.
    Adapted from https://stackoverflow.com/a/26151604/ to use on methods.
    """

    @wraps(decorator)
    def layer(self, *args, **kwargs):
        def apply(f):
            return decorator(self, f, *args, **kwargs)
        return apply
    return layer


def get_arity(f: Callable):
    return len(signature(f).parameters)


def last_argument_is_of_type(f: Callable, t: Type):
    sig = signature(f)
    params = list(sig.parameters.values())
    if not params:
        return False
    return params[-1].annotation is t


def call_with_typed_args(f, *args, optional_args=False):
    sig = signature(f)
    coerced = []
    for param, arg in zip(sig.parameters.values(), args):
        optional = optional_args
        if param.annotation is not sig.empty:
            t = param.annotation
            if hasattr(t, '__origin__') and t.__origin__ is Union and t.__args__[-1] is type(None):
                # argument is of type `Optional[type]`
                t = t.__args__[0]
                optional = True
            try:
                arg = t(arg)
            except TypeError as e:
                if not isinstance(t, _Final):
                    # the type could be instantiated
                    arg = None
                # used a type from `typing`, which are ignored, ex: `AnyStr`
            except ValueError as e:
                if arg:
                    # invalid arg, ex: `int('1.0')`
                    raise e
                if t in (int, float):
                    arg = maxsize
        if arg == '' or arg == maxsize:
            if not optional:
                raise ValueError
            if param.default is not sig.empty:
                arg = param.default
            elif arg == maxsize:
                arg = 0
        coerced.append(arg)
    return f(*coerced)
