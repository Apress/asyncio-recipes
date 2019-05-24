import asyncio
import sys


async def main():
    pass


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

if sys.platform != "win32":
    watcher = asyncio.get_child_watcher()
    watcher.attach_loop(loop)

try:
    loop.run_forever()
finally:
    try:
        loop.run_until_complete(loop.shutdown_asyncgens())
    finally:
        loop.close()
