import logging

from .base import BaseProxyHandler
from .._proxy.abc import AbstractProxy
from .._proxy.http import HttpProxy
from .._stream import SocketStream


class HttpProxyHandler(BaseProxyHandler):
    def __init__(
        self,
        username: str = None,
        password: str = None,
    ):
        self.username = username
        self.password = password
        self.logger = logging.getLogger(__name__)

    def create_proxy(self, stream: SocketStream) -> AbstractProxy:
        return HttpProxy(
            stream=stream,
            username=self.username,
            password=self.password,
        )
