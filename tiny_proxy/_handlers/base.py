import logging
from typing import Union

import anyio
import anyio.abc
from anyio.streams.tls import TLSStream

from .._stream import SocketStream
from .._proxy.abc import AbstractProxy
from .._tunnel import create_tunnel

AnyioSocketStream = Union[anyio.abc.SocketStream, TLSStream]


class BaseProxyHandler:
    logger: logging.Logger

    async def handle(self, stream: AnyioSocketStream):
        client = SocketStream(stream)
        proxy = self.create_proxy(client)

        try:
            remote = await proxy.connect_to_remote()
        except anyio.get_cancelled_exc_class():  # noqa
            await client.aclose()
        except Exception as e:
            await client.aclose()
            self.logger.error(e)
            self.logger.debug(e, exc_info=True)
        else:
            try:
                await create_tunnel(client, remote)
            except anyio.get_cancelled_exc_class():  # noqa  # pragma: nocover
                pass
            except Exception as e:  # pragma: nocover
                self.logger.error(e)
                self.logger.debug(e, exc_info=True)
            finally:
                await remote.aclose()
                await client.aclose()

    def create_proxy(self, stream: SocketStream) -> AbstractProxy:
        raise NotImplementedError()
