import asyncio

async def endless_async_gen():
    while True:
        yield 3
        await asyncio.sleep(1)

async def main():
    async for i in endless_async_gen():
        print(i)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


try:
    loop.run_until_complete(main())
except KeyboardInterrupt:
    print("Caught Ctrl+C. Exiting now..")
finally:
    try:
        loop.run_until_complete(loop.shutdown_asyncgens())
    finally:
        loop.close()