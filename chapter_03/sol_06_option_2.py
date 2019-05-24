import asyncio


async def cancellable(delay=10):
    loop = asyncio.get_running_loop()
    try:
        now = loop.time()
        print(f"Sleeping from {now} for {delay} seconds ...")
        await asyncio.sleep(delay)
        print(f"Slept for {delay} seconds without disturbance...")
    except asyncio.CancelledError:
        print(f"Cancelled at {now} after {loop.time()-now} seconds")


async def main():
    coro = cancellable()
    task = asyncio.create_task(coro)
    await asyncio.sleep(3)

    def canceller(task, fut):
        task.cancel()
        fut.set_result(None)

    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    loop.call_soon_threadsafe(canceller, task, fut)
    await fut


asyncio.run(main())
