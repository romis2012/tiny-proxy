import asyncio
import logging
import ssl
import typing
from contextlib import contextmanager
from multiprocessing import Process

from anyio import create_tcp_listener
from anyio.streams.tls import TLSListener

from tests.utils import cancel_all_tasks, cancel_tasks, wait_until_connectable
from tiny_proxy import HttpProxyHandler, Socks5ProxyHandler, Socks4ProxyHandler


class ProxyConfig(typing.NamedTuple):
    proxy_type: str
    host: str
    port: int
    username: typing.Optional[str] = None
    password: typing.Optional[str] = None
    ssl_certfile: typing.Optional[str] = None
    ssl_keyfile: typing.Optional[str] = None

    def to_dict(self):
        d = {}
        for key, val in self._asdict().items():
            if val is not None:
                d[key] = val
        return d


class ProxyServer:
    cls_map = {
        'http': HttpProxyHandler,
        'socks4': Socks4ProxyHandler,
        'socks5': Socks5ProxyHandler,
    }

    def __init__(self, config: typing.Iterable[ProxyConfig], loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.server_tasks = []

    def run(self):
        proxies = self.config
        for proxy in proxies:
            server_task = self.loop.create_task(self._listen(**proxy.to_dict()))
            self.server_tasks.append(server_task)

    def run_forever(self):
        self.run()
        self.loop.run_forever()

    def shutdown(self):
        print('Shutting down...')

        cancel_tasks(self.server_tasks, self.loop)
        cancel_all_tasks(self.loop)

        self.loop.run_until_complete(self.loop.shutdown_asyncgens())
        try:
            self.loop.run_until_complete(self.loop.shutdown_default_executor())
        except AttributeError:  # pragma: no cover
            pass  # shutdown_default_executor is new to Python 3.9

        self.loop.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.shutdown()

    async def _listen(
        self,
        proxy_type,
        host,
        port,
        ssl_certfile=None,
        ssl_keyfile=None,
        **kwargs,
    ):
        handler_cls = self.cls_map.get(proxy_type)
        if not handler_cls:
            raise RuntimeError(f'Unsupported type: {proxy_type}')

        if ssl_certfile and ssl_keyfile:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(ssl_certfile, ssl_keyfile)
        else:
            ssl_context = None

        print(f'Starting {proxy_type} proxy on {host}:{port}...')

        handler = handler_cls(**kwargs)

        listener = await create_tcp_listener(local_host=host, local_port=port)
        if ssl_context is not None:
            listener = TLSListener(listener=listener, ssl_context=ssl_context)

        async with listener:
            await listener.serve(handler.handle)


def _start_proxy_server(config: typing.Iterable[ProxyConfig]):
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    server = ProxyServer(config=config, loop=loop)

    try:
        server.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        server.shutdown()


class ProxyServerRunner:
    def __init__(self, config: typing.Iterable[ProxyConfig]):
        self.config = config
        self.process = None

    def run(self):
        """
        https://pytest-cov.readthedocs.io/en/latest/subprocess-support.html#if-you-use-multiprocessing-process
        or use Thread
        """
        try:
            from pytest_cov.embed import cleanup_on_sigterm  # noqa
        except ImportError:
            pass
        else:
            cleanup_on_sigterm()

        self.process = Process(target=_start_proxy_server, kwargs=dict(config=self.config))
        self.process.daemon = True
        self.process.start()

    def shutdown(self):
        self.process.terminate()


@contextmanager
def start_proxy_server(config: ProxyConfig):
    """
    https://pytest-cov.readthedocs.io/en/latest/subprocess-support.html#if-you-use-multiprocessing-process
    or use Thread
    """
    try:
        from pytest_cov.embed import cleanup_on_sigterm  # noqa
    except ImportError:
        pass
    else:
        cleanup_on_sigterm()

    process = Process(target=_start_proxy_server, kwargs=dict(config=[config]))
    # process = Thread(target=_start_proxy_server, kwargs=dict(config=[config]))
    process.daemon = True
    process.start()

    wait_until_connectable(host=config.host, port=config.port)

    try:
        yield None
    finally:
        process.terminate()
        process.join()
        pass
