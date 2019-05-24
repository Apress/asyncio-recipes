import asyncio
import contextvars
from contextvars import ContextVar

context = contextvars.copy_context()
context_var = ContextVar('key', default=None)


async def memory(context_var, value):
    old_value = context_var.get()
    context_var.set(value)
    print(old_value, value)


async def main():
    await asyncio.gather(*[memory(context_var, i) for i in range(10)])


asyncio.run(main())
