import asyncio
import random

STOCK_MARKET = {
    "DAX": 100,
    "SPR": 10,
    "AMAZON": 1000,
}

INITIAL_STOCK_MARKET = STOCK_MARKET.copy()


class MarketException(BaseException):
    pass


async def stock_watcher(on_alert, stock, price, cond):
    async with cond:
        print(f"Waiting for {stock} to be under {price}$")
        await cond.wait_for(lambda: STOCK_MARKET.get(stock) < price)
        await on_alert()


def random_stock():
    while True:
        yield random.choice(list(STOCK_MARKET.keys()))


async def twitter_quotes(conds, threshold):
    for stock in random_stock():
        STOCK_MARKET[stock] -= random.randint(1, 10)
        new_value = STOCK_MARKET[stock]
        print(f"New stock market value for {stock}: {new_value}")
        if new_value < threshold:
            cond = conds.get(stock)
            async with cond:
                cond.notify()
        await asyncio.sleep(.1)


async def governmental_market_surveillance():
    raise MarketException()


async def main():
    lock = asyncio.Lock()
    conditions = {stock: asyncio.Condition(lock) for stock in STOCK_MARKET}
    threshold = -50
    stock_watchers = [
        stock_watcher(
            governmental_market_surveillance,
            stock,
            threshold,
            conditions.get(stock)
        ) for stock in STOCK_MARKET
    ]
    await asyncio.gather(*[twitter_quotes(conditions, threshold), *stock_watchers], return_exceptions=False)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except MarketException:
        print("Restoring the stock market..")
        STOCK_MARKET = INITIAL_STOCK_MARKET.copy()
