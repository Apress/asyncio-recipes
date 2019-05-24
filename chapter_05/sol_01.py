from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import asynccontextmanager
import asyncio


class AsyncFile(object):

    def __init__(self, file, loop=None, executor=None):
        if not loop:
            loop = asyncio.get_running_loop()
        if not executor:
            executor = ThreadPoolExecutor(10)
        self.file = file
        self.loop = loop
        self.executor = executor
        self.pending = []
        self.result = []

    def write(self, string):
        self.pending.append(
            self.loop.run_in_executor(self.executor, self.file.write, string, )
        )

    def read(self, i):
        self.pending.append(
            self.loop.run_in_executor(self.executor, self.file.read, i, )
        )

    def readlines(self):
        self.pending.append(
            self.loop.run_in_executor(self.executor, self.file.readlines, )
        )


@asynccontextmanager
async def async_open(path, mode="w"):
    with open(path, mode=mode) as f:
        loop = asyncio.get_running_loop()
        file = AsyncFile(f, loop=loop)
        try:
            yield file
        finally:
            file.result = await asyncio.gather(*file.pending, loop=loop)