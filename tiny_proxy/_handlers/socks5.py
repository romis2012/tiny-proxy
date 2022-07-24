import logging

from .base import BaseProxyHandler
from .._proxy.abc import AbstractProxy
from .._proxy.socks5 import Socks5Proxy
from .._stream import SocketStream


class Socks5ProxyHandler(BaseProxyHandler):
    def __init__(
        self,
        username: str = None,
        password: str = None,
    ):
        self.username = username
        self.password = password
        self.logger = logging.getLogger(__name__)

    def create_proxy(self, stream: SocketStream) -> AbstractProxy:
        return Socks5Proxy(
            stream=stream,
            username=self.username,
            password=self.password,
        )
