import asyncio
import functools
from io import StringIO
from unittest import TestCase, main as unittest_main
from unittest.mock import patch


def into_future(arg, *, loop=None):
    fut = (loop or asyncio.get_running_loop()).create_future()
    fut.set_exception(arg) if isinstance(arg, Exception) else fut.set_result(arg)
    return fut


class AsyncTestCase(TestCase):
    def __getattribute__(self, name):
        attr = super().__getattribute__(name)
        if name.startswith('test') and asyncio.iscoroutinefunction(attr):
            return functools.partial(asyncio.run, attr())
        else:
            return attr


class AsyncTimer:
    async def execute_timely(self, delay, times, f, *args, **kwargs):
        for i in range(times):
            await asyncio.sleep(delay)
            (await f(*args, **kwargs)) if asyncio.iscoroutine(f) else f(*args, **kwargs)


class AsyncTimerTest(AsyncTestCase):

    async def test_execute_timely(self):
        times = 3
        delay = 3

        with  patch("asyncio.sleep", return_value=into_future(None)) as mock_sleep, \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            async_timer = AsyncTimer()
            await async_timer.execute_timely(delay, times, print, "test_execute_timely")

        mock_sleep.assert_called_with(delay)
        assert mock_stdout.getvalue() == "test_execute_timely\ntest_execute_timely\ntest_execute_timely\n"


if __name__ == '__main__':
    unittest_main()
