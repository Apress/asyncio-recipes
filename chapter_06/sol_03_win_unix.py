import argparse
import asyncio
import sys

parser = argparse.ArgumentParser("streamserver")

subparsers = parser.add_subparsers(dest="command")
primary = subparsers.add_parser("primary")
secondary = subparsers.add_parser("secondary")
for subparser in (primary, secondary):
    subparser.add_argument("--host", default="127.0.0.1")
    subparser.add_argument("--port", default=1234)


async def connection_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    print("Handler started")
    writer.write(b"Hi there!")
    await writer.drain()
    message = await reader.read(1024)
    print(message)


async def start_primary(host, port):
    await asyncio.create_subprocess_exec(sys.executable, __file__, "secondary", "--host", host, "--port", str(port), )

    server = await asyncio.start_server(connection_handler, host=host, port=port)
    async with server:
        await server.serve_forever()


async def start_secondary(host, port):
    reader, writer = await asyncio.open_connection(host, port)
    message = await reader.read(1024)
    print(message)
    writer.write(b"Hi yourself!")
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def main():
    args = parser.parse_args()

    if args.command == "primary":
        await start_primary(args.host, args.port)
    else:
        await start_secondary(args.host, args.port)


try:
    import logging

    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Press ctrl+c to stop")
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
except KeyboardInterrupt:
    logging.debug("Stopped..")
