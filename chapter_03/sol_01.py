import asyncio

@asyncio.coroutine
def coro():
    value = yield from inner()
    print(value)

@asyncio.coroutine
def inner():
    return [1, 2, 3]

asyncio.run(coro()) # will print [1, 2, 3]