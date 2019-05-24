import asyncio


async def main():
    pass


loop = asyncio.get_event_loop()
task = loop.create_task(main())
task.add_done_callback(lambda fut: loop.stop())
# Or more generic if you don't have loop in scope:
# task.add_done_callback(lambda fut: asyncio.get_running_loop().stop())

loop.run_forever()
