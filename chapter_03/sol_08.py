import asyncio


async def cancellable(delay=10):
    now = asyncio.get_running_loop().time()
    try:
        print(f"Sleeping from {now} for {delay} seconds ...")
        await asyncio.sleep(delay)
        print(f"Slept for {delay} seconds without disturbance...")
    except asyncio.CancelledError:
        print("I was disturbed in my sleep!")


def canceller(task, fut):
    task.cancel()
    fut.set_result(None)


async def cancel_threadsafe(task, *, delay=3, loop):
    await asyncio.sleep(delay)
    fut = loop.create_future()
    loop.call_soon_threadsafe(canceller, task, fut)
    await fut


async def main():
    complete_time = 10
    cancel_after_secs = 3
    loop = asyncio.get_running_loop()
    coro = cancellable(delay=complete_time)
    shielded_task = asyncio.shield(coro)
    asyncio.create_task(
        cancel_threadsafe(shielded_task,
                          delay=cancel_after_secs,
                          loop=loop)
    )
    try:
        await shielded_task
    except asyncio.CancelledError:
        await asyncio.sleep(complete_time - cancel_after_secs)


asyncio.run(main())
