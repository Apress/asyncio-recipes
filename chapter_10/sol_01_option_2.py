import asyncio
import sys


class MockException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


def raiser_sync(text):
    raise MockException(text)


async def main():
    loop = asyncio.get_running_loop()
    loop.call_soon(raiser_sync, "You cannot catch me like this!")
    await asyncio.sleep(3)


if __name__ == '__main__':
    try:
        asyncio.run(main(), debug=True)
    except MockException as err:
        print(err, file=sys.stderr)


async def main():
    try:
        loop = asyncio.get_running_loop()
        loop.call_soon(raiser_sync, "You cannot catch me like this!")
    except MockException as err:
        print(err, file=sys.stderr)
    finally:
        await asyncio.sleep(3)


if __name__ == '__main__':
    asyncio.run(main(), debug=True)


def exception_handler(loop, context):
    exception = context.get("exception")
    if isinstance(exception, MockException):
        print(exception, file=sys.stderr)
    else:
        loop.default_exception_handler(context)


async def main():
    loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
    loop.set_exception_handler(exception_handler)
    loop.call_soon(raiser_sync, "Finally caught the loop.call_* mock exception!")


if __name__ == '__main__':
    asyncio.run(main(), debug=True)
