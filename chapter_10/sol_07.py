import sys
from unittest.mock import patch

import asynctest
import pytest


def check_pytest_asyncio_installed():
    import os
    from importlib import util
    if not util.find_spec("pytest_asyncio"):
        print("You need to install pytest-asyncio first!", file=sys.stderr)
        sys.exit(os.EX_SOFTWARE)


async def printer(*args, printfun, **kwargs):
    printfun(*args, kwargs)


async def async_printer(*args, printcoro, printfun, **kwargs):
    await printcoro(*args, printfun=printfun, **kwargs)


@pytest.mark.asyncio
async def test_printer_with_print():
    text = "Hello world!"
    dict_of_texts = dict(more_text="This is a nested text!")

    with patch('builtins.print') as mock_printfun:
        await printer(text, printfun=mock_printfun, **dict_of_texts)
        mock_printfun.assert_called_once_with(text, dict_of_texts)


@pytest.mark.asyncio
async def test_async_printer_with_print():
    text = "Hello world!"
    dict_of_texts = dict(more_text="This is a nested text!")
    with patch('__main__.printer', new=asynctest.CoroutineMock()) as mock_printfun:
        await async_printer(text, printcoro=mock_printfun, printfun=print, **dict_of_texts)
        mock_printfun.assert_called_once_with(text, printfun=print, **dict_of_texts)


if __name__ == '__main__':
    check_pytest_asyncio_installed()
    pytest.main(sys.argv)
