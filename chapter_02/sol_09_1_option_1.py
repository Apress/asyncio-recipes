import asyncio
import random


async def work(i):
    print(await asyncio.sleep(random.randint(0, i), result=f"Concurrent work {i}"))


async def main():
    tasks = [asyncio.ensure_future(work(i)) for i in range(10)]
    await asyncio.gather(*tasks)


asyncio.run(main())
