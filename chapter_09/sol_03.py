import asyncio
from collections import defaultdict, OrderedDict
from json import dumps
from urllib.parse import urljoin
from wsgiref.handlers import format_date_time

from httptools import HttpRequestParser


class HTTPProtocol():

    def __init__(self, future=None):
        self.parser = HttpRequestParser(self)
        self.headers = {}
        self.body = b""
        self.url = b""
        self.future = future

    def on_url(self, url: bytes):
        self.url = url

    def on_header(self, name: bytes, value: bytes):
        self.headers[name] = value

    def on_body(self, body: bytes):
        self.body = body

    def on_message_complete(self):
        self.future.set_result(self)

    def feed_data(self, data):
        self.parser.feed_data(data)


MAX_PAYLOAD_LEN = 65536
DEFAULT_HTTP_VERSION = "HTTP/1.1"
NOT_FOUND = """<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <title>404 | Page not found</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="description" content="404 Error page">
    </head>
    <body>
        <p>"Sorry ! the page you are looking for can't be found"</p>
    </body>
</html>"""

REASONS = {
    100: "Continue",
    101: "Switching Protocols",
    200: "OK",
    201: "Created",
    202: "Accepted",
    203: "Non-Authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy",
    307: "Temporary Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Time-out",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Request Entity Too Large",
    414: "Request-URI Too Large",
    415: "Unsupported Media Type",
    416: "Requested range not satisfiable",
    417: "Expectation Failed",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Time-out",
    505: "HTTP Version not supported"

}


class HTTPError(BaseException):
    def __init__(self, status_code):
        assert status_code >= 400
        self.status_code = status_code
        self.reason = REASONS.get(status_code, "")

    def __str__(self):
        return f"{self.status_code} - {self.reason}"


class Response:
    def __init__(self, status_code, headers, http_version=DEFAULT_HTTP_VERSION, body=""):
        self.http_version = http_version
        self.status_code = status_code
        self.headers = headers
        self.reason = REASONS.get(status_code, "")
        self.body = body

    def __str__(self):
        status_line = f"{self.http_version} {self.status_code} {self.reason}\r\n"

        headers = "".join(
            (f'"{key}": {value}\r\n' for key, value in self.headers.items())
        )
        return f"{status_line}{headers}\r\n{self.body}"


def get_default_headers():
    return OrderedDict({
        "Date": format_date_time(None).encode("ascii"),
        "Server": AsyncioHTTPHandler.banner
    })


def response(headers=None, status_code=200, content_type="text/html", http_version=DEFAULT_HTTP_VERSION, body=""):
    if not headers:
        headers = get_default_headers()
    headers.update({"Content-Type": content_type,
                    "Content-Length": str(len(body))})
    return Response(status_code, headers, http_version, body)


def json(headers=None, status_code=200, content_type="application/json", http_version=DEFAULT_HTTP_VERSION, body=None):
    if not body:
        body = {}
    return response(headers, status_code, content_type, http_version, dumps(body))


class AsyncioHTTPHandler:
    allowed_methods = ["GET"]
    version = 1.0
    banner = f"AsyncioHTTPServer/{version}".encode("ascii")
    default_timeout = 30

    def __init__(self, host, timeout=default_timeout):
        self.host = host
        self.routes = defaultdict(dict)
        self.timeout = timeout

    def route(self, *args, method="GET", path=None):

        def register_me(f):
            nonlocal path, self

            if not path:
                path = f.__name__
            http_method = method.upper()

            assert http_method in AsyncioHTTPHandler.allowed_methods

            if not path.startswith("/"):
                path = urljoin("/", path)
            self.routes[http_method][path] = f
            return f

        if args:
            f, = args
            return register_me(f)
        return register_me

    async def on_connection(self, reader, writer):
        try:
            request = await asyncio.wait_for(reader.read(MAX_PAYLOAD_LEN), self.timeout)
            await self.send(writer, await self.handle(request))
        except HTTPError as err:
            if err.status_code == 404:
                await self.send(writer, response(status_code=err.status_code, body=NOT_FOUND))
            elif err.status_code == 405:
                headers = get_default_headers()
                headers.update(Allow=", ".join(AsyncioHTTPHandler.allowed_methods))
                await self.send(writer, json(headers, status_code=err.status_code))
            else:
                await self.send(writer, json(status_code=err.status_code))
        except TimeoutError:
            await self.send(writer, json(status_code=408))
        finally:
            writer.close()

    async def handle(self, request):
        finish_parsing = asyncio.get_running_loop().create_future()
        proto = HTTPProtocol(future=finish_parsing)

        # Ignore upgrade requests for now
        proto.feed_data(request)
        await finish_parsing

        try:
            path = proto.url.decode("UTF-8")
            method = proto.parser.get_method().decode("UTF-8")
        except UnicodeDecodeError:
            raise HTTPError(500)

        if not method.upper() in AsyncioHTTPHandler.allowed_methods:
            raise HTTPError(405)

        handler = self.routes[method].get(path)
        if not handler:
            raise HTTPError(404)
        return await handler(self)

    async def send(self, writer, response):
        writer.write(str(response).encode("ascii"))
        await writer.drain()


host = "127.0.0.1"
port = 1234

server = AsyncioHTTPHandler(host)


@server.route()
async def test_me(server):
    return json(body=dict(it_works=True))


async def main():
    s = await asyncio.start_server(server.on_connection, host, port)
    async with s:
        await s.serve_forever()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Closed..")
