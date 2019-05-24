import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)


class MonitorTask(asyncio.Task):

    def __init__(self, coro, *, loop):
        super().__init__(coro, loop=loop)
        self.start = loop.time()
        self.loop = loop

    def __del__(self):
        super(MonitorTask, self).__del__()
        self.loop = None

    def __await__(self):
        it = super(MonitorTask, self).__await__()

        def awaited(self):
            try:
                for i in it:
                    yield i
            except BaseException as err:
                raise err
            finally:
                try:
                    logging.debug("%r took %s ms to run", self, self.loop.time() - self.start)
                except:
                    logging.debug("Could not estimate endtime of %r")

        return awaited(self)

    @staticmethod
    def task_factory(loop, coro):
        task = MonitorTask(coro, loop=loop)
        # The traceback is truncated to hide internal calls in asyncio
        # show only the traceback from user code
        if task._source_traceback:
            del task._source_traceback[-1]
        return task


async def work():
    await asyncio.sleep(1)


async def main():
    loop = asyncio.get_running_loop()
    loop.set_task_factory(MonitorTask.task_factory)
    await asyncio.create_task(work())


if __name__ == '__main__':
    asyncio.run(main(), debug=True)
