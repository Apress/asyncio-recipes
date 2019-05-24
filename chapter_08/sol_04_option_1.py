import asyncio
import sys


async def coro():
    print("This works!")


async def ensure_future_deprecated():
    # Up to Python 3.6
    task = asyncio.ensure_future(coro())

    # In Python 3.7+
    task_2 = asyncio.create_task(coro())


async def main():
    pass


# Up to Python 3.6
asyncio.get_event_loop().run_until_complete(main())

# Python 3.7+
asyncio.run(main())


async def wait_deprecated():
    # Passing coroutines objects to wait() directly is deprecated:

    coros = [asyncio.sleep(10), asyncio.sleep(10)]
    done, pending = await asyncio.wait(coros)

    # Use asyncio.create_task

    futures = [asyncio.create_task(coro) for coro in (asyncio.sleep(10), asyncio.sleep(10))]
    done, pending = await asyncio.wait(futures)


async def tasks_deprecated(loop):
    # Using Task class methods is deprecated:
    task = asyncio.Task.current_task(loop)
    tasks = asyncio.Task.all_tasks(loop)

    # Use the asyncio module level functions instead:
    task = asyncio.current_task(loop)
    tasks = asyncio.all_tasks(loop)


async def coroutine_deprecated():
    @asyncio.coroutine
    def gen_coro():
        yield from asyncio.sleep(1)

    async def native_coroutine():
        await asyncio.sleep(1)


async def passing_loop_deprecated():
    loop = asyncio.get_running_loop()
    # This is deprecated
    await asyncio.sleep(10, loop=loop)
    await asyncio.wait_for(asyncio.create_task(asyncio.sleep(10)), 11, loop=loop)
    futures = {asyncio.create_task(asyncio.sleep(10, loop=loop))}
    done, pending = await asyncio.wait(futures, loop=loop)

    await asyncio.sleep(10)
    await asyncio.wait_for(asyncio.create_task(asyncio.sleep(10)), 11, loop=loop)
    futures = {asyncio.create_task(asyncio.sleep(10))}
    done, pending = await asyncio.wait(futures)


async def coroutine_wrapper_deprecated():
    # set_coroutine_wrapper() and sys.get_coroutine_wrapper() will be removed in Python 3.8
    sys.set_coroutine_wrapper(sys.get_coroutine_wrapper())
    # and are deprecated in favor of
    sys.set_coroutine_origin_tracking_depth(sys.get_coroutine_origin_tracking_depth())
    # Of course passing sensible values!
