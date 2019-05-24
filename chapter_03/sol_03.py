import asyncio


async def coroutine(*args, **kwargs):
    print("Waiting for the next coroutine...")
    await another_coroutine(*args, **kwargs)
    print("This will follow 'Done'")


async def another_coroutine(*args, **kwargs):
    await asyncio.sleep(3)
    print("Done")
