import asyncio
import threading


def create_event_loop_thread(worker, *args, **kwargs):
    def _worker(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(worker(*args, **kwargs))
        finally:
            loop.close()

    return threading.Thread(target=_worker, args=args, kwargs=kwargs)


async def print_coro(*args, **kwargs):
    print(f"Inside the print coro on {threading.get_ident()}:", (args, kwargs))


def start_threads(*threads):
    [t.start() for t in threads if isinstance(t, threading.Thread)]


def join_threads(*threads):
    [t.join() for t in threads if isinstance(t, threading.Thread)]


def main():
    workers = [create_event_loop_thread(print_coro) for i in range(10)]
    start_threads(*workers)
    join_threads(*workers)


if __name__ == '__main__':
    main()
