import asyncio
import os
import random
import typing
from multiprocessing import Lock
from multiprocessing import Process

lock = Lock()
pid_loops = {}
processes = []


def cleanup():
    global processes
    while processes:
        proc = processes.pop()
        proc.join()


def get_event_loop():
    global lock, pid_loops
    pid = os.getpid()
    with lock:
        if pid not in pid_loops:
            pid_loops[pid] = asyncio.new_event_loop()
            pid_loops[pid].pid = pid
        return pid_loops[pid]


def asyncio_init():
    with lock:
        pid = os.getpid()
        pid_loops[pid] = asyncio.new_event_loop()
        pid_loops[pid].pid = pid


async def worker(*, loop: asyncio.AbstractEventLoop):
    print(await asyncio.sleep(random.randint(0, 3), result=f"Work {os.getpid()}"))


def process_main(coro_worker: typing.Coroutine, num_of_coroutines: int):
    """
    This is the main method of the process.
    We create the infrastructure for the coroutine worker here.
    We assert that we run one loop per process and use our own helper to get an event loop instance for that matter.
    :param coro_worker:
    :param url:
    :param num_of_coroutines:
    :return:
    """
    asyncio_init()
    loop = get_event_loop()
    assert os.getpid() == loop.pid
    try:
        workers = [coro_worker(loop=loop) for i in range(num_of_coroutines)]
        loop.run_until_complete(asyncio.gather(*workers, loop=loop))
    except KeyboardInterrupt:
        print(f"Stopping {os.getpid()}")
        loop.stop()
    finally:
        loop.close()


def main(number_of_processes, number_of_coroutines, *, process_main):
    global processes
    for _ in range(number_of_processes):
        proc = Process(target=process_main, args=(worker, number_of_coroutines))
        processes.append(proc)
        proc.start()
    cleanup()


try:
    main(number_of_processes=10, number_of_coroutines=2, process_main=process_main)
except KeyboardInterrupt:
    print("CTRL+C was pressed.. Stopping all subprocesses..")
    cleanup()
    print("Cleanup finished")
