import asyncio
import logging
import random

logging.basicConfig(level=logging.INFO)


async def busy_loop(interval, work, worker, shutdown_event):
    while not shutdown_event.is_set():
        await worker(work)
        await asyncio.sleep(interval)
    logging.info("Shutdown event was set..")
    return work


async def cleanup(mess, shutdown_event):
    await shutdown_event.wait()
    logging.info("Cleaning up the mess: %s...", mess)
    # Add cleanup logic here


async def shutdown(delay, shutdown_event):
    await asyncio.sleep(delay)
    shutdown_event.set()


async def add_mess(mess_pile, ):
    mess = random.randint(1, 10)
    logging.info("Adding the mess: %s...", mess)
    mess_pile.append(mess)


async def main():
    shutdown_event = asyncio.Event()
    shutdown_delay = 10
    work = []
    await asyncio.gather(*[
        shutdown(shutdown_delay, shutdown_event),
        cleanup(work, shutdown_event),
        busy_loop(1, work, add_mess, shutdown_event),
    ])


if __name__ == '__main__':
    asyncio.run(main())
