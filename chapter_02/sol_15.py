import asyncio

# Quote from https://docs.python.org/3/library/asyncio-subprocess.html:
# The child watcher must be instantiated in the main thread, before executing subprocesses from other threads. Call the get_child_watcher() function in the main thread to instantiate the child watcher.
import functools
import shutil
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

def stop_loop(*args, loop, **kwargs):
    loop.stop()


async def is_windows_process_alive(process, delay=0.5):
    """
    On windows the signal API is very sparse, meaning we don't have SIGCHILD.
    So we just check if we have a return code on our process object.
    :param process:
    :param delay:
    :return:
    """
    while process.returncode == None:
        await asyncio.sleep(delay)


async def main(process_coro, *, loop):
    process = await process_coro
    if sys.platform != "win32":
        child_watcher: asyncio.AbstractChildWatcher = asyncio.get_child_watcher()
        child_watcher.add_child_handler(process.pid, functools.partial(stop_loop, loop=loop))
    else:
        await is_windows_process_alive(process)
        loop.stop()


loop = asyncio.get_event_loop()

process_coro = asyncio.create_subprocess_exec(shutil.which("ping"), "-c", "1", "127.0.0.1",
                                              stdout=asyncio.subprocess.DEVNULL,
                                              stderr=asyncio.subprocess.DEVNULL)

loop.create_task(main(process_coro, loop=loop))
loop.run_forever()