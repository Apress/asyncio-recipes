import asyncio
import socket
from contextlib import asynccontextmanager


@asynccontextmanager
async def tcp_client(host='google.de', port=80):
   address_info = (await asyncio.get_running_loop().getaddrinfo(
       host, port,
       proto=socket.IPPROTO_TCP,
   )).pop()

   if not address_info:
       raise ValueError(f"Could not resolve {host}:{port}")
   host,port =address_info[-1]
   reader, writer = await asyncio.open_connection(host, port)
   try:
       yield (reader, writer)
   finally:
       writer.close()
       await asyncio.shield(writer.wait_closed())


async def main():
   async with tcp_client() as (reader, writer):
       writer.write(b"GET /us HTTP/1.1\r\nhost: apress.com\r\n\r\n")
       await writer.drain()
       content = await reader.read(1024**2)
       print(content)

asyncio.run(main())