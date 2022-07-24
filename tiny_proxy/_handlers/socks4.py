import logging

from .base import BaseProxyHandler
from .._proxy.abc import AbstractProxy
from .._proxy.socks4 import Socks4Proxy
from .._stream import SocketStream


class Socks4ProxyHandler(BaseProxyHandler):
    def __init__(self, username: str = None):
        self.username = username
        self.logger = logging.getLogger(__name__)

    def create_proxy(self, stream: SocketStream) -> AbstractProxy:
        return Socks4Proxy(stream=stream, username=self.username)
