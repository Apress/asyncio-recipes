import asyncio

async def cancellable(delay=10):
    loop = asyncio.get_running_loop()
    try:
        now = loop.time()
        print(f"Sleeping from {now} for {delay} seconds ...")
        await asyncio.sleep(delay, loop=loop)
        print(f"Slept {delay} seconds ...")
    except asyncio.CancelledError:
        print(f"Cancelled at {now} after {loop.time()-now} seconds")


async def main():
    coro = cancellable()
    task = asyncio.create_task(coro)
    await asyncio.sleep(3)
    task.cancel()


asyncio.run(main())
