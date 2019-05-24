import asyncio
import random


async def work(i):
    print(await asyncio.sleep(random.randint(0, i), result=f"Concurrent work {i}"))


loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(work(i)) for i in range(10)]
loop.run_until_complete(asyncio.gather(*tasks))
