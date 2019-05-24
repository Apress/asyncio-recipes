import asyncio

import re

import typing

from concurrent.futures import Executor, ThreadPoolExecutor

from urllib.request import urlopen

DEFAULT_EXECUTOR = ThreadPoolExecutor(4)
ANCHOR_TAG_PATTERN = re.compile(b"<a.+?href=[\"|\'](.*?)[\"|\'].*?>", re.RegexFlag.MULTILINE | re.RegexFlag.IGNORECASE)

async def wrap_async(generator: typing.Generator,
                     executor: Executor = DEFAULT_EXECUTOR,
                     sentinel=object(),
                     *,
                     loop: asyncio.AbstractEventLoop = None):
    """
    We wrap a generator and return an asynchronous generator instead
    :param iterator:
    :param executor:
    :param sentinel:
    :param loop:
    :return:
    """

    if not loop:
        loop = asyncio.get_running_loop()

    while True:
        result = await loop.run_in_executor(executor, next, generator, sentinel)
        if result == sentinel:
            break
        yield result


def follow(*links):
    """
    :param links:
    :return:
    """

    return ((link, urlopen(link).read()) for link in links)


def get_links(text: str):
    """
    Get back an iterator that gets us all the links in a text iteratively and safely
    :param text:
    :return:
    """

    # Always grab the last match, because that is how a smart http parser would interpret a malformed
    # anchor tag
    return (match.groups()[-1]
            for match in ANCHOR_TAG_PATTERN.finditer(text)
            # This portion is a safeguard against None matches and zero href matches
            if hasattr(match, "groups") and len(match.groups()))


async def main(*links):
    async for current, body in wrap_async(follow(*links)):
        print("Current url:", current)
        print("Content:", body)
        async for link in wrap_async(get_links(body)):
            print(link)


asyncio.run(main("http://apress.com"))