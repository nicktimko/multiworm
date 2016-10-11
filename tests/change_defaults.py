from __future__ import absolute_import, print_function, unicode_literals
import six
from six.moves import zip, filter, map, reduce, input, range

import contextlib
import inspect


def _inspect_signature(f):
    sig = inspect.signature(f)
    if any(v.kind == v.KEYWORD_ONLY for v in sig.parameters.values()):
        raise ValueError('currently do not support keyword-only arguments')
    return (
        list(sig.parameters),
        tuple(v.default for v in sig.parameters.values() if v.default is not v.empty),
    )


def _inspect_getargspec(f):
    spec = inspect.getargspec(f)
    return spec.args, spec.defaults


def _inspect_f(f):
    try:
        inspect.signature
    except AttributeError:
        return _inspect_getargspec(f)
    else:
        return _inspect_signature(f)


@contextlib.contextmanager
def change_defaults(f, **overrides):
#     spec = inspect.getargspec(f)
#     args = spec.args
#     old_defaults = spec.defaults
    args, old_defaults = _inspect_f(f)
    if old_defaults is None:
        raise ValueError("function '{}' has no defaults to override"
                         .format(f.__name__))

    args_with_defaults = args[-len(old_defaults):]

    bad_overrides = set(overrides) - set(args_with_defaults)
    if bad_overrides:
        raise ValueError("function '{}' does not have defaults for argument(s): {}"
                         .format(f.__name__, list(bad_overrides)))

    default_map = dict(zip(args_with_defaults, old_defaults))
    default_map.update(overrides)
    f.__defaults__ = tuple(default_map[k] for k in args_with_defaults)

    yield

    f.__defaults__ = old_defaults
