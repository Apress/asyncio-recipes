
import random
import asyncio

async def random_number_gen(delay,start,end):
    while True:
        yield random.randint(start,end)
        await asyncio.sleep(delay)
