import asyncio


async def run(i, semaphore):
    async with semaphore:
        print(f"{i} working..")
        return await asyncio.sleep(1)


async def main():
    semaphore = asyncio.BoundedSemaphore(10)
    await asyncio.gather(*[run(i, semaphore) for i in range(100)])


if __name__ == '__main__':
    asyncio.run(main(), debug=True)
