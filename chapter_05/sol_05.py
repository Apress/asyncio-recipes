import asyncio
from contextlib import asynccontextmanager
from functools import partial as func


class SchedulerLoop(asyncio.SelectorEventLoop):

    def __init__(self):
        super(SchedulerLoop, self).__init__()
        self._scheduled_callback_futures = []
        self.results = []

    @staticmethod
    def unwrapper(fut: asyncio.Future, function):
        """
        Function to get rid of the implicit fut parameter.
        :param fut:
        :type fut:
        :param function:
        :return:
        """
        return function()

    def _future(self, done_hook):
        """
        Create a future object that calls the done_hook when it is awaited
        :param loop:
        :param function:
        :return:
        """
        fut = self.create_future()
        fut.add_done_callback(func(self.unwrapper, function=done_hook))
        return fut

    def schedule_soon_threadsafe(self, callback, *args, context=None):
        fut = self._future(func(callback, *args))
        self._scheduled_callback_futures.append(fut)
        self.call_soon_threadsafe(fut.set_result, None, context=context)

    def schedule_soon(self, callback, *args, context=None):
        fut = self._future(func(callback, *args))
        self._scheduled_callback_futures.append(fut)
        self.call_soon(fut.set_result, None, context=context)

    def schedule_later(self, delay_in_seconds, callback, *args, context=None):
        fut = self._future(func(callback, *args))
        self._scheduled_callback_futures.append(fut)
        self.call_later(delay_in_seconds, fut.set_result, None, context=context)

    def schedule_at(self, delay_in_seconds, callback, *args, context=None):
        fut = self._future(func(callback, *args))
        self._scheduled_callback_futures.append(fut)
        self.call_at(delay_in_seconds, fut.set_result, None, context=context)

    async def await_callbacks(self):
        callback_futs = self._scheduled_callback_futures[:]
        self._scheduled_callback_futures[:] = []
        return await asyncio.gather(*callback_futs, return_exceptions=True, loop=self)


class SchedulerLoopPolicy(asyncio.DefaultEventLoopPolicy):
    def new_event_loop(self):
        return SchedulerLoop()


@asynccontextmanager
async def scheduler_loop():
    loop = asyncio.get_running_loop()
    if not isinstance(loop, SchedulerLoop):
        raise ValueError("You can run the scheduler_loop async context manager only on a SchedulerLoop")

    try:
        yield loop
    finally:
        loop.results = await loop.await_callbacks()


async def main():
    async with scheduler_loop() as loop:
        loop.schedule_soon(print, "This")
        loop.schedule_soon(print, "works")
        loop.schedule_soon(print, "seamlessly")


asyncio.set_event_loop_policy(SchedulerLoopPolicy())
asyncio.run(main())