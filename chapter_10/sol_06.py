import asyncio
import sys
from types import SimpleNamespace

import pytest


def check_pytest_asyncio_installed():
    import os
    from importlib import util
    if not util.find_spec("pytest_asyncio"):
        print("You need to install pytest-asyncio first!", file=sys.stderr)
        sys.exit(os.EX_SOFTWARE)


async def return_after_sleep(res):
    return await asyncio.sleep(2, result=res)


async def setattr_async(loop, delay, ns, key, payload):
    loop.call_later(delay, setattr, ns, key, payload)


@pytest.fixture()
async def loop():
    return asyncio.get_running_loop()


@pytest.fixture()
def namespace():
    return SimpleNamespace()


@pytest.mark.asyncio
async def test_return_after_sleep():
    expected_result = b'expected result'
    res = await return_after_sleep(expected_result)
    assert expected_result == res


@pytest.mark.asyncio
async def test_setattr_async(loop, namespace):
    key = "test"
    delay = 1.0
    expected_result = object()
    await setattr_async(loop, delay, namespace, key, expected_result)
    await asyncio.sleep(delay)
    assert getattr(namespace, key, None) is expected_result


if __name__ == '__main__':
    check_pytest_asyncio_installed()
    pytest.main(sys.argv)
