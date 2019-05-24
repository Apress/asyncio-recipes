import asyncio


async def execute_on(condition, coro, predicate):
    async with condition:
        await condition.wait_for(predicate)
        await coro


async def print_coro(text):
    print(text)


async def worker(numbers):
    while numbers:
        print("Numbers:", numbers)
        numbers.pop()
        await asyncio.sleep(0.25)


async def main():
    numbers = list(range(10))
    condition = asyncio.Condition()
    is_empty = lambda: not numbers
    await worker(numbers)
    await execute_on(condition, print_coro("Finished!"), is_empty)


asyncio.run(main())
