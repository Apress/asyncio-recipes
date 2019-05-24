import asyncio
from concurrent.futures.process import ProcessPoolExecutor
from contextlib import asynccontextmanager
from multiprocessing import get_context, freeze_support

CONTEXT = get_context("spawn")


class AsyncProcessPool:

   def __init__(self, executor, loop=None, ):
       self.executor = executor
       if not loop:
           loop = asyncio.get_running_loop()
       self.loop = loop
       self.pending = []
       self.result = None

   def submit(self, fn, *args, **kwargs):
       fut = asyncio.wrap_future(self.executor.submit(fn, *args, **kwargs), loop=self.loop)
       self.pending.append(fut)
       return fut


@asynccontextmanager
async def pool(max_workers=None, mp_context=CONTEXT,
              initializer=None, initargs=(), loop=None, return_exceptions=True):
   with ProcessPoolExecutor(max_workers=max_workers, mp_context=mp_context,
                            initializer=initializer, initargs=initargs) as executor:
       pool = AsyncProcessPool(executor, loop=loop)
       try:
           yield pool
       finally:
           pool.result = await asyncio.gather(*pool.pending, loop=pool.loop, return_exceptions=return_exceptions)


async def main():
   async with pool() as p:
       p.submit(print, "This works perfectly fine")
       result = await p.submit(sum, (1, 2))
       print(result)
   print(p.result)

if __name__ == '__main__':
   freeze_support()
   asyncio.run(main())