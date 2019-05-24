import asyncio
from concurrent.futures.thread import ThreadPoolExecutor

import certifi
import urllib3

HTTP_POOL_MANAGER = urllib3.PoolManager(ca_certs=certifi.where())
EXECUTOR = ThreadPoolExecutor(10)
URL = "https://apress.com"


async def block_request(http, url, *, executor=None, loop: asyncio.AbstractEventLoop):
    return await loop.run_in_executor(executor, http.request, "GET", url)


def multi_block_requests(http, url, n, *, executor=None, loop: asyncio.AbstractEventLoop):
    return (asyncio.ensure_future(block_request(http, url, executor=executor, loop=loop)) for _ in
            range(n))


async def consume_responses(*coro, loop):
    result = await asyncio.gather(*coro, loop=loop, return_exceptions=True)
    for res in result:
        if not isinstance(res, Exception):
            print(res.data)


loop = asyncio.get_event_loop()
loop.set_default_executor(EXECUTOR)
loop.run_until_complete(consume_responses(block_request(HTTP_POOL_MANAGER, URL, loop=loop), loop=loop))
loop.run_until_complete(
    consume_responses(*multi_block_requests(HTTP_POOL_MANAGER, URL, 10, loop=loop), loop=loop))
