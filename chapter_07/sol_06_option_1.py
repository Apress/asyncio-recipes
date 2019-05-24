import asyncio
import typing


async def delayed_add(delay, d: typing.Dict, key: typing.Hashable, value: float):
    last = d[key]  # This is where the critical path starts, d is the shared resource and this is a read access
    await asyncio.sleep(delay)
    d[key] = last + value  # This is where the critical path ends, d is the shared resource and this is a write access


async def main():
    d = {"value": 0}
    await asyncio.gather(delayed_add(2, d, "value", 1.0), delayed_add(1.0, d, "value", 1.0))
    print(d)
    assert d["value"] != 2

if __name__ == '__main__':
    asyncio.run(main())
