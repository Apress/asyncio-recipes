import asyncio
import getpass
import inspect
import itertools
import logging
import shutil
import subprocess
import sys
from functools import wraps

logging.basicConfig(level=logging.INFO)


class NotFoundError(BaseException):
    pass


class ProcessError(BaseException):
    def __init__(self, return_code, stderr):
        self.return_code = return_code
        self.stderr = stderr

    def __str__(self):
        return f"Process returned non 0 return code {self.return_code}.\n" \
               f"{self.stderr.decode('utf-8')}"


def get_ssh_client_path():
    executable = shutil.which("ssh")
    if not executable:
        raise NotFoundError(
            "Could not find ssh client. You can install OpenSSH from https://www.OpenSSH.com/portable.html.\nOn Mac OSX we recommend using brew: brew install OpenSSH.\nOn Linux systems you should use the package manager of your choice, like so. apt-get install OpenSSH\nOn windows you can use Chocolatey: choco install OpenSSH.")
    return executable


def get_ssh_client_path():
    executable = shutil.which("ssh")
    if not executable:
        raise NotFoundError(
            "Could not find ssh client. You can install OpenSSH from https://www.OpenSSH.com/portable.html.\nOn Mac OSX we recommend using brew: brew install OpenSSH.\nOn Linux systems you should use the package manager of your choice, like so: apt-get install OpenSSH\nOn windows you can use Chocolatey: choco install OpenSSH.")
    return executable


class Connection:
    def __init__(self, user=None, host="127.0.0.1", port=22, timeout=None, ssh_client=None):
        self.host = host
        self.port = port
        if not user:
            user = getpass.getuser()
        self.user = user
        self.timeout = timeout
        if not ssh_client:
            ssh_client = get_ssh_client_path()
        self.ssh_client = ssh_client

    async def run(self, *cmds, interactive=False):
        commands = [self.ssh_client,
                    f"{self.user}@{self.host}",
                    f"-p {self.port}",
                    *cmds]
        logging.info(" ".join(commands))
        proc = await asyncio.create_subprocess_exec(*commands,
                                                    stdin=subprocess.PIPE,
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.PIPE, )
        if not interactive:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), self.timeout)

            if proc.returncode != 0:
                raise ProcessError(proc.returncode, stderr)

            return proc, stdout, stderr
        else:
            return proc, proc.stdout, proc.stderr


def command(*args, interactive=False, **kwargs):
    def outer(f):
        cmd = f.__name__
        for key, value in kwargs.items():
            if sys.platform.startswith(key) and value:
                cmd = value

        if inspect.isasyncgenfunction(f):
            @wraps(f)
            async def wrapper(connection, *args):
                proc, stdout, stderr = await connection.run(shutil.which(cmd), *args, interactive=interactive)

                async for value in f(proc, stdout, stderr):
                    yield value
        else:
            @wraps(f)
            async def wrapper(connection, *args):
                proc, stdout, stderr = await connection.run(shutil.which(cmd), *args, interactive=interactive)
                return await f(proc, stdout, stderr)

        return wrapper

    if not args:
        return outer
    else:
        return outer(*args)


@command(win32="dir")
async def ls(proc, stdout, stderr):
    for line in stdout.decode("utf-8").splitlines():
        yield line


@command(win32="tasklist", interactive=True)
async def top(proc, stdout, stderr):
    c = itertools.count()

    async for value in stdout:
        if next(c) > 1000:
            break
        print(value)


async def main():
    con = Connection()
    try:
        async for line in ls(con):
            print(line)

        await top(con)

    except Exception as err:
        logging.error(err)


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

asyncio.run(main())
