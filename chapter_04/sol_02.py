import random
import asyncio


async def random_number_gen(delay, start, end):
    while True:
        yield random.randint(start, end)
        await asyncio.sleep(delay)


async def main():
    async for i in random_number_gen(1, 0, 100):
        print(i)


try:
    print("Starting to print out random numbers...")
    print("Shut down the application with Ctrl+C")
    asyncio.run(main())
except KeyboardInterrupt:
    print("Closed the main loop..")
