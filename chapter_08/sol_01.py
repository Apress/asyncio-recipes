import asyncio
import logging
import tracemalloc
from functools import wraps

logging.basicConfig(level=logging.DEBUG)


class Profiler:
    def __init__(self):
        self.stats = {}
        self.logger = logging.getLogger(__name__)

    def profile_memory_usage(self, f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            snapshot = tracemalloc.take_snapshot()
            res = await f(*args, **kwargs)
            self.stats[f.__name__] = tracemalloc.take_snapshot().compare_to(snapshot, 'lineno')
            return res

        return wrapper

    def print(self):
        for name, stats in self.stats.items():
            for entry in stats:
                self.logger.debug(entry)

    def __enter__(self):
        tracemalloc.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        tracemalloc.stop()
        self.print()


profiler = Profiler()


@profiler.profile_memory_usage
async def main():
    pass


with profiler:
    asyncio.run(main())
