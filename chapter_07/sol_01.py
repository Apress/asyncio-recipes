import asyncio

NON_ATOMIC_SUM_KEY = 'non_atomic_sum'
ATOMIC_SUM_KEY = 'atomic_sum'
DATABASE = {ATOMIC_SUM_KEY: 0, NON_ATOMIC_SUM_KEY: 0}


async def add_with_delay(key, value, delay):
    old_value = DATABASE[key]
    await asyncio.sleep(delay)
    DATABASE[key] = old_value + value


async def add_locked_with_delay(lock, key, value, delay):
    async with lock:
        old_value = DATABASE[key]
        await asyncio.sleep(delay)
        DATABASE[key] = old_value + value


async def main():
    # An asyncio lock can be used to guarantee exclusive access to a shared resource
    lock = asyncio.Lock()
    atomic_workers = [
        add_locked_with_delay(lock, ATOMIC_SUM_KEY, 1, 3),
        add_locked_with_delay(lock, ATOMIC_SUM_KEY, 1, 2),
    ]
    non_atomic_workers = [
        add_with_delay(NON_ATOMIC_SUM_KEY, 1, 3),
        add_with_delay(NON_ATOMIC_SUM_KEY, 1, 2),
    ]

    await asyncio.gather(*non_atomic_workers)
    await asyncio.gather(*atomic_workers)

    assert DATABASE.get(ATOMIC_SUM_KEY) == 2
    assert DATABASE.get(NON_ATOMIC_SUM_KEY) != 2

if __name__ == '__main__':
    asyncio.run(main())
