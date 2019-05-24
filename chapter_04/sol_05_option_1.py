import asyncio


async def async_gen_coro():
    yield 1
    yield 2
    yield 3


async def main():
    async_generator = async_gen_coro()
    await async_generator.asend(None)
    await async_generator.asend(None)

asyncio.run(main())
