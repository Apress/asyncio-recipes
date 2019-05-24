import asyncio


async def coroutine_to_run():
    print(await asyncio.sleep(1, result="I have finished!"))


async def main():
    task = asyncio.create_task(coroutine_to_run())
    await task


asyncio.run(main())
