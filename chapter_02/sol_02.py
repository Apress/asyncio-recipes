import asyncio
import sys

loop = asyncio.new_event_loop()

print(loop)  # Print the loop
asyncio.set_event_loop(loop)

if sys.platform != "win32":
    watcher = asyncio.get_child_watcher()
    watcher.attach_loop(loop)
