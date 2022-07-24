from ._errors import ProxyError
from ._stream import SocketStream
from ._tunnel import create_tunnel

from ._proxy.abc import AbstractProxy
from ._proxy.socks5 import Socks5Proxy
from ._proxy.socks4 import Socks4Proxy
from ._proxy.http import HttpProxy

from ._handlers.http import HttpProxyHandler
from ._handlers.socks4 import Socks4ProxyHandler
from ._handlers.socks5 import Socks5ProxyHandler

__version__ = '0.1.0'

__all__ = (
    'ProxyError',
    'SocketStream',
    'create_tunnel',
    'AbstractProxy',
    'Socks5Proxy',
    'Socks4Proxy',
    'HttpProxy',
    'HttpProxyHandler',
    'Socks4ProxyHandler',
    'Socks5ProxyHandler',
)
