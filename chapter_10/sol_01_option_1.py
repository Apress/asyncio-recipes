import asyncio
import sys


class MockException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


async def raiser(text):
    raise MockException(text)


async def main():
    raise MockException("Caught mock exception outside the loop. The loop is not running anymore.")


try:
    asyncio.run(main())
except MockException as err:
    print(err, file=sys.stderr)

async def main():
    await raiser("Caught inline mock exception outside the loop."
                 "The loop is not running anymore.")


try:
    asyncio.run(main(), debug=True)
except MockException as err:
    print(err, file=sys.stderr)


async def main():
    try:
        await raiser("Caught mock exception raised in an awaited coroutine outside the loop."
                     "The loop is still running.")
    except MockException as err:
        print(err, file=sys.stderr)

if __name__ == '__main__':
    asyncio.run(main(), debug=True)
