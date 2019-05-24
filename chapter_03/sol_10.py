import asyncio


async def print_delayed(delay, text, result):
    print(await asyncio.sleep(delay, text))
    return result


async def main():
    workload = [
        print_delayed(1, "Printing this after 1 second", 1),
        print_delayed(1, "Printing this after 1 second", 2),
        print_delayed(1, "Printing this after 1 second", 3),
    ]

    results = await asyncio.gather(*workload)
    print(results)


asyncio.run(main())
