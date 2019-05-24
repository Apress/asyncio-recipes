import asyncio


async def print_delayed(delay, text):
    print(await asyncio.sleep(delay, text))


async def main():
    await print_delayed(1, "Printing this after 1 second")
    await print_delayed(1, "Printing this after 2 seconds")
    await print_delayed(1, "Printing this after 3 seconds")


asyncio.run(main())
