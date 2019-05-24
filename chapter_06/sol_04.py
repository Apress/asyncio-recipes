import abc
import asyncio
import collections
import inspect
import logging
import pickle
import typing
from contextlib import asynccontextmanager
from pickle import PickleError
from uuid import uuid4

from hbmqtt.client import MQTTClient, ConnectException
from hbmqtt.mqtt.constants import QOS_0

GET_REMOTE_METHOD = "get_remote_method"
GET_REMOTE_METHOD_RESPONSE = "get_remote_method/response"

CALL_REMOTE_METHOD = "call_remote_method"
CALL_REMOTE_METHOD_RESPONSE = "call_remote_method/response"

REGISTER_REMOTE_METHOD = "register_remote_method"
REGISTER_REMOTE_METHOD_RESPONSE = "register_remote_method/response"

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def connect(url):
    client = MQTTClient()
    try:
        await client.connect(url)
        yield client
    except ConnectException:
        logging.exception(f"Could not connect to {url}")
    finally:
        await client.disconnect()


@asynccontextmanager
async def pool(n, url):
    clients = [MQTTClient() for _ in range(n)]
    try:
        await asyncio.gather(*[client.connect(url) for client in clients])
        yield clients
    except ConnectException:
        logging.exception(f"Could not connect to {url}")
    finally:
        await asyncio.gather(*[client.disconnect() for client in clients])


def set_future_result(fut, result):
    if not fut:
        pass
    if isinstance(result, Exception):
        fut.set_exception(result)
    else:
        fut.set_result(result)


class RPCException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f"Error: {self.message}"


class RegisterRemoteMethodException(RPCException):
    def __init__(self):
        super(RegisterRemoteMethodException, self).__init__(f"Could not respond to {REGISTER_REMOTE_METHOD} query")


class GetRemoteMethodException(RPCException):
    def __init__(self):
        super(GetRemoteMethodException, self).__init__(f"Could not respond to {GET_REMOTE_METHOD} query")


class CallRemoteMethodException(RPCException):
    def __init__(self):
        super(CallRemoteMethodException, self).__init__(f"Could not respond to {CALL_REMOTE_METHOD} query")


class RCPBase:

    def __init__(self, client: MQTTClient, topics: typing.List[str], qos=QOS_0):
        self.client = client
        self.running_fut = None
        self.topics = topics
        self.qos = qos

    @abc.abstractmethod
    async def on_get_remote_method(self, uuid_, service_name, function_name):
        raise NotImplementedError("Not implemented on_get_remote_method!")

    @abc.abstractmethod
    async def on_register_remote_method(self, uuid_, service_name, function_name, signature):
        raise NotImplementedError("Not implemented on_register_remote_method!")

    @abc.abstractmethod
    async def on_call_remote_method(self, uuid_, service_name, function_name, args, kwargs):
        raise NotImplementedError("Not implemented on_call_remote_method!")

    @abc.abstractmethod
    async def on_get_remote_method_response(self, uuid_, service_name, function_name, signature_or_exception):
        raise NotImplementedError("Not implemented on_get_remote_method_response!")

    @abc.abstractmethod
    async def on_register_remote_method_response(self, uuid_, service_name, function_name, is_registered_or_exception):
        raise NotImplementedError("Not implemented on_register_remote_method_response!")

    @abc.abstractmethod
    async def on_call_remote_method_response(self, uuid_, service_name, function_name, result_or_exception):
        raise NotImplementedError("Not implemented on_call_remote_method_response!")

    async def next_message(self):
        message = await self.client.deliver_message()
        packet = message.publish_packet
        topic_name, payload = packet.variable_header.topic_name, packet.payload.data
        return topic_name, payload

    async def loop(self):
        while True:
            topic, payload = await self.next_message()
            try:
                yield topic, pickle.loads(payload)
            except (PickleError, AttributeError, EOFError, ImportError, IndexError):
                logging.exception("Could not deserialize payload: %s for topic: %s", payload, topic)

    async def __aenter__(self):
        self.running_fut = asyncio.ensure_future(self.start())
        await self.client.subscribe([
            (topic, self.qos) for topic in self.topics
        ])
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
        await self.client.unsubscribe(self.topics)

    async def start(self):
        async for topic, payload in self.loop():
            try:
                if topic == REGISTER_REMOTE_METHOD:
                    await self.on_register_remote_method(*payload)
                elif topic == GET_REMOTE_METHOD:
                    await self.on_get_remote_method(*payload)
                elif topic == CALL_REMOTE_METHOD:
                    await self.on_call_remote_method(*payload)
                elif topic == REGISTER_REMOTE_METHOD_RESPONSE:
                    await self.on_register_remote_method_response(*payload)
                elif topic == GET_REMOTE_METHOD_RESPONSE:
                    await self.on_get_remote_method_response(*payload)
                elif topic == CALL_REMOTE_METHOD_RESPONSE:
                    await self.on_call_remote_method_response(*payload)
            except TypeError:
                logging.exception(f"Could not call handler for topic: %s and payload: %s", topic, payload)
            except NotImplementedError:
                pass

    async def stop(self):
        if self.running_fut:
            self.running_fut.cancel()

    async def wait(self):
        if self.running_fut:
            await asyncio.shield(self.running_fut)


class RemoteMethod:

    def __init__(self, rpc_client, signature, function_name, qos=QOS_0):
        self.rpc_client = rpc_client
        self.signature = signature
        self.function_name = function_name
        self.qos = qos

    async def __call__(self, *args, **kwargs, ):
        uuid_ = str(uuid4())
        service_name = self.rpc_client.service_name
        payload = (uuid_, service_name, self.function_name, args, kwargs)
        fut = asyncio.Future()
        self.rpc_client.call_remote_method_requests.setdefault(service_name, {}).setdefault(self.function_name, {})[
            uuid_] = fut
        await self.rpc_client.client.publish(CALL_REMOTE_METHOD, pickle.dumps(payload), qos=self.qos)
        return await fut


class RPCClient(RCPBase):
    def __init__(self, client, service_name, topics=None, qos=QOS_0):
        if not topics:
            topics = [CALL_REMOTE_METHOD_RESPONSE, GET_REMOTE_METHOD_RESPONSE, ]
        super(RPCClient, self).__init__(client, topics, qos=qos)
        self.call_remote_method_requests = collections.defaultdict(dict)
        self.get_remote_method_requests = collections.defaultdict(dict)
        self.list_remote_methods_requests = collections.defaultdict(dict)
        self.responses = collections.defaultdict(dict)
        self.service_name = service_name
        self.remote_methods_cache = collections.defaultdict(dict)

    def __getattr__(self, item):
        return asyncio.ensure_future(self.get_remote_method(item))

    async def get_remote_method(self, function_name):
        while True:
            uuid_ = str(uuid4())
            payload = (uuid_, self.service_name, function_name)
            fut = asyncio.Future()
            self.get_remote_method_requests.setdefault(self.service_name, {}).setdefault(function_name, {})[uuid_] = fut
            await self.client.publish(GET_REMOTE_METHOD, pickle.dumps(payload), qos=QOS_0)
            # Might throw GetRemoteMethodException
            try:
                signature = await asyncio.shield(fut)
                return RemoteMethod(self, signature, function_name)
            except GetRemoteMethodException:
                await asyncio.sleep(0)

    async def on_call_remote_method_response(self, uuid_, service_name, function_name, result_or_exception):
        fut = self.call_remote_method_requests.get(service_name, {}).get(function_name, {}).pop(uuid_, None)
        set_future_result(fut, result_or_exception)

    async def on_get_remote_method_response(self, uuid_, service_name, function_name, signature_or_exception):
        fut = self.get_remote_method_requests.get(service_name, {}).get(function_name, {}).pop(uuid_, None)
        set_future_result(fut, signature_or_exception)


class RPCService(RCPBase):
    def __init__(self, client: MQTTClient, name: str, topics: typing.List[str] = None, qos=QOS_0):
        if not topics:
            topics = [REGISTER_REMOTE_METHOD_RESPONSE, CALL_REMOTE_METHOD]
        super(RPCService, self).__init__(client, topics, qos=qos)
        self.name = name
        self.client = client
        self.qos = qos
        self.register_remote_method_requests = collections.defaultdict(dict)
        self.remote_methods = collections.defaultdict(dict)

    async def register_function(self, remote_function):
        function_name = remote_function.__name__
        uuid_ = str(uuid4())
        payload = pickle.dumps((uuid_, self.name, function_name, inspect.signature(remote_function)))
        fut = asyncio.Future()
        self.register_remote_method_requests.setdefault(self.name, {}).setdefault(function_name, {})[uuid_] = fut
        self.remote_methods[self.name][function_name] = remote_function
        await self.client.publish(REGISTER_REMOTE_METHOD, payload, qos=self.qos)
        return await asyncio.shield(fut)

    async def on_register_remote_method_response(self, uuid_, service_name, function_name, is_registered_or_exception):
        fut = self.register_remote_method_requests.get(service_name, {}).get(function_name, {}).get(uuid_, None)
        set_future_result(fut, is_registered_or_exception)

    async def on_call_remote_method(self, uuid_, service_name, function_name, args, kwargs):
        remote_method = self.remote_methods.get(service_name, {}).get(function_name, None)
        if not remote_method:
            payload = pickle.dumps((uuid_, service_name, function_name, CallRemoteMethodException()))
            return await self.client.publish(CALL_REMOTE_METHOD_RESPONSE, payload, qos=self.qos)
        try:
            result = await remote_method(*args, **kwargs)
            payload = pickle.dumps((uuid_, service_name, function_name, result))
            return await self.client.publish(CALL_REMOTE_METHOD_RESPONSE, payload, qos=self.qos)
        except Exception as err:
            payload = pickle.dumps((uuid_, service_name, function_name, err))
            return await self.client.publish(CALL_REMOTE_METHOD_RESPONSE, payload, qos=self.qos)


class RemoteRegistrar(RCPBase):
    def __init__(self, client: MQTTClient, topics: typing.List[str] = None, qos=QOS_0):
        if not topics:
            topics = [REGISTER_REMOTE_METHOD, GET_REMOTE_METHOD]
        super(RemoteRegistrar, self).__init__(client, topics, qos=qos)
        self.registrar = collections.defaultdict(dict)

    async def on_register_remote_method(self, uuid_, service_name, function_name, signature):
        try:
            self.registrar.setdefault(service_name, {})[function_name] = signature
            payload = pickle.dumps((uuid_, service_name, function_name, True), )
            await self.client.publish(REGISTER_REMOTE_METHOD_RESPONSE, payload)

        except Exception:
            # A broad exception clause like this is bad practice but we are only interested in the outcome
            # of saving the signature, so we convert it
            logging.exception(f"Failed to save signature: {signature}")
            payload = pickle.dumps((uuid_, service_name, function_name, RegisterRemoteMethodException()))
            await self.client.publish(REGISTER_REMOTE_METHOD_RESPONSE, payload, )

    async def on_get_remote_method(self, uuid_, service_name, function_name):
        signature = self.registrar.get(service_name, {}).get(function_name, None)

        if signature:
            payload = pickle.dumps((uuid_, service_name, function_name, signature), )
            await self.client.publish(GET_REMOTE_METHOD_RESPONSE, payload)
        else:
            payload = pickle.dumps((uuid_, service_name, function_name, GetRemoteMethodException()), )
            await self.client.publish(GET_REMOTE_METHOD_RESPONSE, payload)


async def remote_function(i: int, f: float, s: str):
    print("It worked")
    return f


async def register_with_delay(rpc_service, remote_function, delay=3):
    await asyncio.sleep(delay)
    await rpc_service.register_function(remote_function)


async def main(url="mqtt://localhost", service_name="TestService"):
    async with pool(3, url) as (client, client1, client2):
        async with RemoteRegistrar(client):
            async with RPCService(client1, service_name) as rpc_service:
                async with RPCClient(client2, service_name) as rpc_client:
                    asyncio.ensure_future(register_with_delay(rpc_service, remote_function))
                    handler = await asyncio.wait_for(rpc_client.remote_function,timeout=10)
                    res = await handler(1, 3.4, "")
                    print(res)


if __name__ == '__main__':
    asyncio.run(main())