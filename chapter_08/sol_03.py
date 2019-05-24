import asyncio
import logging
import sys
from functools import wraps

THRESHOLD = 0.5
sys.set_coroutine_origin_tracking_depth(10)


def time_it_factory(handler):
    def time_it(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            loop = asyncio.get_running_loop()
            start = loop.time()
            coro = f(*args, **kwargs)
            result = await coro
            delta = loop.time() - start
            handler(coro, delta)
            return result

        return wrapper

    return time_it


@time_it_factory
def log_time(coro, time_delta):
    if time_delta > THRESHOLD:
        logging.warning("The coroutine %s took more than %s ms", coro, time_delta)
        for frame in coro.cr_origin:
            logging.warning("file:%s line:%s function:%s", *frame)
        else:
            logging.warning("Coroutine has no origin !")


@log_time
async def main():
    await asyncio.sleep(1)


asyncio.run(main())
