import functools
import logging
import ssl
import sys
import time
from typing import Tuple, Optional

import anyio
import yaml
from anyio import create_tcp_listener, get_cancelled_exc_class, create_task_group
from anyio.streams.tls import TLSListener

from tiny_proxy import HttpProxyHandler, Socks4ProxyHandler, Socks5ProxyHandler

CLS_MAP = {
    'http': HttpProxyHandler,
    'socks4': Socks4ProxyHandler,
    'socks5': Socks5ProxyHandler,
}

logger = logging.getLogger(__name__)


def configure_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel('INFO')

    fmt = '%(asctime)s [%(name)s:%(lineno)d] %(levelname)s : %(message)s'
    formatter = logging.Formatter(fmt)
    formatter.converter = time.gmtime

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    root_logger.addHandler(stdout_handler)


def load_settings(file_name='./settings.yml') -> dict:
    with open(file_name, 'r') as f:
        return yaml.safe_load(f)


async def serve(
    proxy_type: str,
    host: str,
    port: int,
    ssl_cert: Optional[Tuple[str, str]] = None,
    **kwargs,
):
    handler_cls = CLS_MAP.get(proxy_type)
    if not handler_cls:
        raise RuntimeError(f'Unsupported proxy type: {proxy_type}')

    if ssl_cert is not None:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(*ssl_cert)
    else:
        ssl_context = None

    logger.info(f'Starting {proxy_type} proxy on {host}:{port}...')

    handler = handler_cls(**kwargs)

    try:
        listener = await create_tcp_listener(local_host=host, local_port=port)
        if ssl_context is not None:
            listener = TLSListener(listener=listener, ssl_context=ssl_context)

        async with listener:
            await listener.serve(handler.handle)
    except get_cancelled_exc_class():  # noqa
        pass


async def start_server(configs: list[dict]):
    async with create_task_group() as tg:
        for cfg in configs:
            tg.start_soon(functools.partial(serve, **cfg))


def main():
    configure_logging()
    settings = load_settings()
    try:
        anyio.run(start_server, settings['proxies'])
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == '__main__':
    main()
