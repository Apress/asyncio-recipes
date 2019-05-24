import asyncio
import tempfile
import os

from chapter_05.sol_01 import async_open


async def main():
   tempdir = tempfile.gettempdir()
   path = os.path.join(tempdir, "run.txt")
   print(f"Writing asynchronously to {path}")

   async with async_open(path, mode="w") as f:
       f.write("This\n")
       f.write("might\n")
       f.write("not\n")
       f.write("end\n")
       f.write("up\n")
       f.write("in\n")
       f.write("the\n")
       f.write("same\n")
       f.write("order!\n")


asyncio.run(main())