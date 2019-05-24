import asyncio
import shutil
import sys
from typing import Tuple, Union


async def invoke_command_async(*command, loop, encoding="UTF-8", decode=True) -> Tuple[
    Union[str, bytes], Union[str, bytes], int]:
    """
    Invoke a command asynchronously and return the stdout, stderr and the process return code.
    :param command:
    :param loop:
    :param encoding:
    :param decode:
    :return:
    """
    if sys.platform != 'win32':
        asyncio.get_child_watcher().attach_loop(loop)
    process = await asyncio.create_subprocess_exec(*command,
                                                   stdout=asyncio.subprocess.PIPE,
                                                   stderr=asyncio.subprocess.PIPE,
                                                   loop=loop)
    out, err = await process.communicate()

    ret_code = process.returncode

    if not decode:
        return out, err, ret_code

    output_decoded, err_decoded = out.decode(encoding) if out else None, \
                                  err.decode(encoding) if err else None

    return output_decoded, err_decoded, ret_code


async def main(loop):
    out, err, retcode = await invoke_command_async(shutil.which("ping"), "-c", "1", "8.8.8.8", loop=loop)
    print(out, err, retcode)


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))
