import asyncio
import sys


async def print_delayed(delay, text, ):
    print(await asyncio.sleep(delay, text))


async def raise_delayed(delay, text, ):
    raise Exception(await asyncio.sleep(delay, text))


async def main():
    workload = [
        print_delayed(5, "Printing this after 5 seconds"),
        raise_delayed(5, "Raising this after 5 seconds"),
        print_delayed(5, "Printing this after 5 seconds"),
    ]

    res = None
    try:
        gathered = asyncio.gather(*workload, return_exceptions=True)
        res = await gathered
    except asyncio.CancelledError:
        print("The gathered task was cancelled", file=sys.stderr)
    finally:
        print("Result:", res)


asyncio.run(main())
