from typing import Callable, Type
from inspect import cleandoc, signature
from functools import wraps


def get_arity(f: Callable):
    return len(signature(f).parameters)


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


def sanitize_docs(docs):
    return cleandoc(docs).replace('\n', ' ')


def enclose(strings, char):
    return [f"{char}{s}{char}" for s in strings]


def last_argument_is_of_type(f: Callable, t: Type):
    sig = signature(f)
    params = list(sig.parameters.values())
    if not params:
        return False
    return params[-1].annotation is t
