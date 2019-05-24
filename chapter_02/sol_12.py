import asyncio
import functools


async def main(loop):
    print("Print in main")


def stop_loop(fut, *, loop):
    loop.call_soon_threadsafe(loop.stop)


loop = asyncio.get_event_loop()
tasks = [loop.create_task(main(loop)) for _ in range(10)]
asyncio.gather(*tasks).add_done_callback(functools.partial(stop_loop, loop=loop))
try:
    loop.run_forever()
finally:
    try:
        loop.run_until_complete(loop.shutdown_asyncgens())
    finally:
        loop.close()  # optional
