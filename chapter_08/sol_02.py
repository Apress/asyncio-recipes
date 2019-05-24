import asyncio
import contextlib
import inspect
import json
import logging
import pickle
import sys
import tracemalloc
from collections import defaultdict, namedtuple
from contextlib import asynccontextmanager
from functools import wraps
from inspect import iscoroutinefunction
from time import time
from tracemalloc import Filter, take_snapshot, start as tracemalloc_start, \
    stop as tracemalloc_stop

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

Timing = namedtuple("Timing", ["start", "end", "delta"])


class Profiler:

    def __init__(self, key_type="lineno", cumulative=False, debug=False, excluded_files=None):
        self.time_stats = defaultdict(list)
        self.memory_stats = defaultdict(dict)
        self.key_type = key_type
        self.cumulative = cumulative
        self.logger = logging.getLogger(__name__)
        self.debug = debug
        if not excluded_files:
            excluded_files = [tracemalloc.__file__, inspect.__file__, contextlib.__file__]
        self.excluded_files = excluded_files
        self.profile_memory_cache = False

    def time(self):
        try:
            return asyncio.get_running_loop().time()
        except RuntimeError:
            return time()

    def get_filter(self, include=False):
        return (Filter(include, filter_) for filter_ in self.excluded_files)

    def profile_memory(self, f):
        self.profile_memory_cache = True
        if iscoroutinefunction(f):
            @wraps(f)
            async def wrapper(*args, **kwargs):
                snapshot = take_snapshot().filter_traces(self.get_filter())
                result = await f(*args, **kwargs)
                current_time = time()
                memory_delta = take_snapshot().filter_traces(self.get_filter()).compare_to(snapshot, self.key_type,
                                                                                           self.cumulative)
                self.memory_stats[f.__name__][current_time] = memory_delta
                return result
        else:
            @wraps(f)
            def wrapper(*args, **kwargs):
                snapshot = take_snapshot().filter_traces(self.get_filter())
                result = f(*args, **kwargs)
                current_time = time()
                memory_delta = take_snapshot().filter_traces(self.get_filter()).compare_to(snapshot, self.key_type,
                                                                                           self.cumulative)
                self.memory_stats[f.__name__][current_time] = memory_delta
                return result
        return wrapper

    def profile_time(self, f):

        if iscoroutinefunction(f):
            @wraps(f)
            async def wrapper(*args, **kwargs):
                start = self.time()
                result = await f(*args, **kwargs)
                end = self.time()
                delta = end - start
                self.time_stats[f.__name__].append(Timing(start, end, delta))
                return result
        else:
            @wraps(f)
            def wrapper(*args, **kwargs):
                start = self.time()
                result = f(*args, **kwargs)
                end = self.time()
                delta = end - start
                self.time_stats[f.__name__].append(Timing(start, end, delta))
                return result
        return wrapper

    def __enter__(self):
        if self.profile_memory_cache:
            self.logger.debug("Starting tracemalloc..")
            tracemalloc_start()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.profile_memory_cache:
            self.logger.debug("Stopping tracemalloc..")
            tracemalloc_stop()
        if self.debug:
            self.print_memory_stats()
            self.print_time_stats()

    def print_memory_stats(self):
        for name, stats in self.memory_stats.items():
            for timestamp, entry in list(stats.items()):
                self.logger.debug("Memory measurements for call of %s at %s", name, timestamp)

                for stats_diff in entry:
                    self.logger.debug("%s", stats_diff)

    def print_time_stats(self):
        for function_name, timings in self.time_stats.items():
            for timing in timings:
                self.logger.debug("function %s was called at %s ms and took: %s ms",
                                  function_name,
                                  timing.start,
                                  timing.delta)


async def read_message(reader, timeout=3):
    data = []
    while True:
        try:
            chunk = await asyncio.wait_for(reader.read(1024), timeout=timeout)
            data += [chunk]
        except asyncio.TimeoutError:
            return b"".join(data)


class ProfilerServer:
    def __init__(self, profiler, host, port):
        self.profiler = profiler
        self.host = host
        self.port = port

    async def on_connection(self,
                            reader: asyncio.StreamReader,
                            writer: asyncio.StreamWriter):
        message = await read_message(reader)
        logging.debug("Message %s:", message)

        try:
            event = json.loads(message, encoding="UTF-8")
            command = event["command"]
            if command not in ["memory_stats", "time_stats"]:
                raise ValueError(f"{command} is illegal!")

            handler = getattr(self.profiler, command, None)
            if not handler:
                raise ValueError(f"{message} is malformed")
            reply_message = handler

            writer.write(pickle.dumps(reply_message))
            await writer.drain()
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError,)as err:
            self.profiler.logger.error("Error occurred while transmission: %s", err)
            writer.write(pickle.dumps(err))
            await writer.drain()
        finally:
            writer.close()


class ProfilerClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def send(self, **kwargs):
        message = json.dumps(kwargs)
        reader, writer = await asyncio.open_connection(self.host, self.port)
        writer.write(message.encode())
        message = await reader.read()
        writer.close()
        try:
            return pickle.loads(message)
        except pickle.PickleError:
            return None

    async def get_memory_stats(self):
        return await self.send(command="memory_stats")

    async def get_time_stats(self):
        return await self.send(command="time_stats")


@asynccontextmanager
async def start_profiler_server(profiler, host, port):
    profiler_server = ProfilerServer(profiler, host, port)
    try:
        server = await asyncio.start_server(profiler_server.on_connection, host, port)
        async with server:
            yield
            await server.serve_forever()
    finally:
        pass


profiler = Profiler(debug=True)


@profiler.profile_time
@profiler.profile_memory
async def to_be_profiled():
    await asyncio.sleep(3)
    list(i for i in range(10000))


async def main(profiler):
    host, port = "127.0.0.1", 1234
    client = ProfilerClient(host, port)
    async with start_profiler_server(profiler, host, port):
        await to_be_profiled()
        memory_stats = await client.get_memory_stats()
        logging.debug(memory_stats)


if __name__ == '__main__':
    try:
        logging.debug("Press CTRL+C to close...")
        with profiler:
            asyncio.run(main(profiler))
    except KeyboardInterrupt:
        logging.debug("Closed..")
