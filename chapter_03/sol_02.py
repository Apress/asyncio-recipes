import asyncio


async def coroutine(*args, **kwargs):
    pass


assert asyncio.iscoroutine(coroutine())
assert asyncio.iscoroutinefunction(coroutine)
