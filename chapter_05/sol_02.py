import asyncio


class Sync():
    def __init__(self):
        self.pending = []
        self.finished = None

    def schedule_coro(self, coro, shield=False):
        fut = asyncio.shield(coro) if shield else asyncio.ensure_future(coro)
        self.pending.append(fut)
        return fut

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.finished = await asyncio.gather(*self.pending, return_exceptions=True)


async def workload():
    await asyncio.sleep(3)
    print("These coroutines will be executed simultaneously and return 42")
    return 42


async def main():
    async with Sync() as sync:
        sync.schedule_coro(workload())
        sync.schedule_coro(workload())
        sync.schedule_coro(workload())
    print("All scheduled coroutines have retuned or thrown:", sync.finished)


asyncio.run(main())