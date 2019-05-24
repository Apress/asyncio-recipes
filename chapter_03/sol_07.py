import asyncio

async def cancellable(delay=10, *, loop):
    try:
        now = loop.time()
        print(f"Sleeping from {now} for {delay} seconds ...")
        await asyncio.sleep(delay)
        print(f"Slept for {delay} seconds without disturbance...")
    except asyncio.CancelledError:
        print(f"Cancelled at {now} after {loop.time()-now} seconds")


def canceller(task, fut):
    task.cancel()
    fut.set_result(None)


async def cancel_threadsafe(gathered_tasks, loop):
    fut = loop.create_future()
    loop.call_soon_threadsafe(canceller, gathered_tasks, fut)
    await fut


async def main():
    loop = asyncio.get_running_loop()
    coros = [cancellable(i, loop=loop) for i in range(10)]
    gathered_tasks = asyncio.gather(*coros)
    # Add a delay here, so we can see that the first three coroutines run uninterrupted
    await asyncio.sleep(3)
    await cancel_threadsafe(gathered_tasks, loop)
    try:
        await gathered_tasks
    except asyncio.CancelledError:
        print("Was cancelled")


asyncio.run(main())
