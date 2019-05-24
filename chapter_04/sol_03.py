import asyncio
import functools
from concurrent.futures.thread import ThreadPoolExecutor

import sys
import certifi
import urllib3


async def request(poolmanager: urllib3.PoolManager,
                  executor,
                  *,
                  method="GET",
                  url,
                  fields=None,
                  headers=None,
                  loop: asyncio.AbstractEventLoop = None, ):
    if not loop:
        loop = asyncio.get_running_loop()
    request = functools.partial(poolmanager.request, method, url, fields=fields, headers=headers)
    return  loop.run_in_executor(executor, request)


async def bulk_requests(poolmanager: urllib3.PoolManager,
                        executor,
                        *,
                        method="GET",
                        urls,
                        fields=None,
                        headers=None,
                        loop: asyncio.AbstractEventLoop = None, ):
    for url in urls:
        yield await request(poolmanager, executor, url=url, fields=fields, headers=headers, loop=loop)


def filter_unsuccesful_requests(responses_and_exceptions):
    return filter(
        lambda url_and_response: not isinstance(url_and_response[1], Exception),
        responses_and_exceptions.items()
    )


async def main():
    poolmanager = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
    executor = ThreadPoolExecutor(10)
    urls = [
        "https://google.de",
        "https://apple.com",
        "https://apress.com",
    ]
    requests = [request async for request in bulk_requests(poolmanager, executor, urls=urls, )]
    responses_and_exceptions = dict(zip(urls, await asyncio.gather(*requests, return_exceptions=True)))
    responses = {url: resp.data for (url, resp) in filter_unsuccesful_requests(responses_and_exceptions)}

    for res in responses.items():
        print(res)

    for url in urls:
        if url not in responses:
            print(f"No successful request could be made to {url}. Reason: {responses_and_exceptions[url]}",file=sys.stderr)


asyncio.run(main())