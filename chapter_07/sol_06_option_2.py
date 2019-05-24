import asyncio
import threading
import time
from concurrent.futures.thread import ThreadPoolExecutor


def add_from_thread(delay, d, key, value):
    print(f"Thread {threading.get_ident()} started...")
    old = d[key]
    print(f"Thread {threading.get_ident()} read value {old}")
    time.sleep(delay)
    print(f"Thread {threading.get_ident()} slept for {delay} seconds")
    d[key] = old + value
    print(f"Thread {threading.get_ident()} wrote {d[key]}")


async def main():
    loop = asyncio.get_running_loop()
    d = {"value": 0}
    executor = ThreadPoolExecutor(10)
    futs = [loop.run_in_executor(executor, add_from_thread, 1, d, "value", 1),
            loop.run_in_executor(executor, add_from_thread, 3, d, "value", 1)]
    await asyncio.gather(*futs)

    assert d["value"] != 2

if __name__ == '__main__':
    asyncio.run(main())
