import asyncio
import logging
from contextlib import asynccontextmanager


class Interactor:
    def __init__(self, agen):
        self.agen = agen

    async def interact(self, *args, **kwargs, ):
        try:
            await self.agen.asend((args, kwargs))
        except StopAsyncIteration:
            logging.exception("The async generator is already exhausted!")


async def wrap_in_asyngen(handler):
    while True:
        args, kwargs = yield
        handler(*args, **kwargs)


@asynccontextmanager
async def start(agen):
    try:
        await agen.asend(None)
        yield Interactor(agen)
    finally:
        await agen.aclose()


async def main():
    async with start(wrap_in_asyngen(print)) as w:
        await w.interact("Put")
        await w.interact("the")
        await w.interact("worker")
        await w.interact("to")
        await w.interact("work!")


asyncio.run(main())