import asyncio


async def main():
    pass


loop = asyncio.get_event_loop()

try:
    loop.run_until_complete(main())
finally:
    try:
        loop.run_until_complete(loop.shutdown_asyncgens())
    finally:
        loop.close()
