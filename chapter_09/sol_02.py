import asyncio
import logging
import sys

import cloudpickle as pickle

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)


class CommandClientProtocol(asyncio.Protocol):
    def __init__(self, connection_lost):
        self._connection_lost = connection_lost
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        result = pickle.loads(data)
        if isinstance(result, Exception):
            raise result
        logging.info(result)

    def connection_lost(self, exc):
        logging.info('The server closed the connection')
        self._connection_lost.set_result(True)

    def execute_remotely(self, f, *args, **kwargs):
        self.transport.write(pickle.dumps((f, args, kwargs)))


async def remote_function(msg):
    print(msg)  # This will be printed out on the host
    return 42


async def main():
    loop = asyncio.get_running_loop()

    connection_lost = loop.create_future()

    transport, protocol = await loop.create_connection(
        lambda: CommandClientProtocol(connection_lost),
        '127.0.0.1', 8888)

    protocol.execute_remotely(remote_function, "This worked!")

    try:
        await connection_lost
    finally:
        transport.close()

if __name__ == '__main__':
    asyncio.run(main())
