import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)


async def producer(iterable, queue: asyncio.Queue, shutdown_event: asyncio.Event):
    for i in iterable:
        if shutdown_event.is_set():
            break
        try:
            queue.put_nowait(i)
            await asyncio.sleep(0)

        except asyncio.QueueFull as err:
            logging.warning("The queue is too full. Maybe the worker are too slow.")
            raise err

    shutdown_event.set()


async def worker(name, handler, queue: asyncio.Queue, shutdown_event: asyncio.Event):
    while not shutdown_event.is_set() or not queue.empty():
        try:
            work = queue.get_nowait()
            # Simulate work
            handler(await asyncio.sleep(1.0, work))
            logging.debug(f"worker {name}: {work}")

        except asyncio.QueueEmpty:
            await asyncio.sleep(0)


async def main():
    n, handler, iterable = 10, lambda val: None, [i for i in range(500)]
    shutdown_event = asyncio.Event()
    queue = asyncio.Queue()
    worker_coros = [worker(f"worker_{i}", handler, queue, shutdown_event) for i in range(n)]
    producer_coro = producer(iterable, queue, shutdown_event)

    coro = asyncio.gather(
        producer_coro,
        *worker_coros,
        return_exceptions=True
    )

    try:
        await  coro
    except KeyboardInterrupt:
        shutdown_event.set()
        coro.cancel()


try:
    asyncio.run(main())
except KeyboardInterrupt:
    # It bubbles up
    logging.info("Pressed ctrl+c...")