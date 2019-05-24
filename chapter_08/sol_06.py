import asyncio
import random


async def fetch(url, *, fut: asyncio.Future):
    await asyncio.sleep(random.randint(3, 5))  # Simulating work
    fut.set_result(random.getrandbits(1024 * 8))


async def checker(responses, url, *, fut: asyncio.Future):
    result = await fut
    responses[url] = result
    print(result)


async def main():
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    responses = {}
    url = "https://apress.com"
    await asyncio.gather(fetch(url, fut=future), checker(responses, url, fut=future))


asyncio.run(main())
