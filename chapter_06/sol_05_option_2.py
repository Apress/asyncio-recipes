import contextvars
import functools
from contextvars import ContextVar

context = contextvars.copy_context()
context_var = ContextVar('key', default=None)


def resetter(context_var, token, invalid_values):
    value = context_var.get()
    if value in invalid_values:
        context_var.reset(token)


def blacklist(context_var, value, resetter):
    old_value = context_var.get()
    token = context_var.set(value)
    resetter(context_var, token)
    print(old_value)


for i in range(10):
    context.run(blacklist, context_var, i, functools.partial(resetter, invalid_values=[5, 6, 7, 8, 9]))
