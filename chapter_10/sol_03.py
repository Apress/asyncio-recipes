import asyncio
import time


def slow():
    time.sleep(1.5)


async def main():
    loop = asyncio.get_running_loop()
    # This will print a debug message if the call takes more than 1 second
    loop.slow_callback_duration = 1
    loop.call_soon(slow)


asyncio.run(main(), debug=True)
