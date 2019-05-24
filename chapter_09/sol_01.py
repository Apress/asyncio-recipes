import asyncio
import functools
import inspect
import logging
import sys
from multiprocessing import freeze_support, get_context

import cloudpickle as pickle

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)


def on_error(exc, *, transport, peername):
    try:
        logging.exception("On error: Exception while handling a subprocess: %s ", exc)
        transport.write(pickle.dumps(exc))

    finally:
        transport.close()
        logging.info("Disconnected %s", peername)


def on_success(result, *, transport, peername, data):
    try:
        logging.debug("On success: Received payload from %s:%s and successfully executed:\n%s", *peername, data)
        transport.write(pickle.dumps(result))
    finally:
        transport.close()
        logging.info("Disconnected %s", peername)


def handle(data):
    f, args, kwargs = pickle.loads(data)
    if inspect.iscoroutinefunction(f):
        return asyncio.run(f(*args, *kwargs))

    return f(*args, **kwargs)


class CommandProtocol(asyncio.Protocol):

    def __init__(self, pool, loop, timeout=30):
        self.pool = pool
        self.loop = loop
        self.timeout = timeout
        self.transport = None

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        logging.info('%s connected', peername)
        self.transport = transport

    def data_received(self, data):
        peername = self.transport.get_extra_info('peername')
        on_error_ = functools.partial(on_error, transport=self.transport, peername=peername)
        on_success_ = functools.partial(on_success, transport=self.transport, peername=peername, data=data)
        result = self.pool.apply_async(handle, (data,), callback=on_success_, error_callback=on_error_)
        self.loop.call_soon(result.wait)
        self.loop.call_later(self.timeout, self.close, peername)

    def close(self, peername=None):
        try:
            if self.transport.is_closing():
                return
            if not peername:
                peername = self.transport.get_extra_info('peername')
        finally:
            self.transport.close()
            logging.info("Disconnecting %s", peername)


async def main():
    loop = asyncio.get_running_loop()
    fork_context = get_context("fork")
    pool = fork_context.Pool()
    server = await loop.create_server(lambda: CommandProtocol(pool, loop), '127.0.0.1', 8888)
    try:
        async with server:
            await server.serve_forever()
    finally:
        pool.close()
        pool.join()


if __name__ == '__main__':
    freeze_support()
    asyncio.run(main())
