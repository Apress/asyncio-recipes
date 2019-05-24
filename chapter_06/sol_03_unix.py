import argparse
import asyncio
import sys

parser = argparse.ArgumentParser("streamserver")

subparsers = parser.add_subparsers(dest="command")
primary = subparsers.add_parser("primary")
secondary = subparsers.add_parser("secondary")
for subparser in (primary, secondary):
    subparser.add_argument("--path", default="/tmp/asyncio.socket")


async def connection_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    print("Handler started")
    writer.write(b"Hi there!")
    await writer.drain()
    message = await reader.read(1024)
    print(message)


async def start_primary(path):
    await asyncio.create_subprocess_exec(sys.executable, __file__, "secondary", "--path", path)

    server = await asyncio.start_unix_server(connection_handler, path)
    async  with server:
        await server.serve_forever()


async def start_secondary(path):
    reader, writer = await asyncio.open_unix_connection(path)
    message = await reader.read(1024)
    print(message)
    writer.write(b"Hi yourself!")
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def main():
    args = parser.parse_args()

    if args.command == "primary":
        await start_primary(args.path)
    else:
        await start_secondary(args.path)
try:
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Press ctrl+c to stop")
    asyncio.run(main())
except KeyboardInterrupt:
    logging.debug("Stopped..")