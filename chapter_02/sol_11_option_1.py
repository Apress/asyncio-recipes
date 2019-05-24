import asyncio


async def main(loop):
    assert loop == asyncio.get_running_loop()


loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))
