import enum
import logging
import ipaddress
from typing import Tuple

import anyio
import anyio.abc

from .._stream import SocketStream
from .._errors import ProxyError
from .abc import AbstractProxy

RSV = NULL = 0x00
SOCKS_VER4 = 0x04


class Command(enum.IntEnum):
    CONNECT = 0x01
    BIND = 0x02


class ReplyCode(enum.IntEnum):
    REQUEST_GRANTED = 0x5A
    REQUEST_REJECTED_OR_FAILED = 0x5B
    CONNECTION_FAILED = 0x5C
    AUTHENTICATION_FAILED = 0x5D


ReplyMessages = {
    ReplyCode.REQUEST_GRANTED: "Request granted",
    ReplyCode.REQUEST_REJECTED_OR_FAILED: "Request rejected or failed",
    ReplyCode.CONNECTION_FAILED: (
        "Request rejected because SOCKS server cannot connect to identd on the client"
    ),
    ReplyCode.AUTHENTICATION_FAILED: (
        "Request rejected because the client program and identd report different user-ids"
    ),
}


class Socks4Proxy(AbstractProxy):
    def __init__(self, stream: SocketStream, username: str = None):
        self.stream = stream
        self.username = username
        self.logger = logging.getLogger(__name__)

    async def connect_to_remote(self) -> SocketStream:
        try:
            remote_host, remote_port = await self.negotiate()
        except (
            anyio.EndOfStream,
            anyio.IncompleteRead,
            anyio.ClosedResourceError,
            anyio.BrokenResourceError,
        ) as e:
            raise ConnectionResetError(
                f'Connection reset by peer {self.stream.getpeername()}'
            ) from e

        self.logger.info('CONNECT {}:{}'.format(remote_host, remote_port))

        try:
            stream = await anyio.connect_tcp(remote_host=remote_host, remote_port=remote_port)
            remote = SocketStream(stream)
        except OSError as e:
            await self.respond(ReplyCode.CONNECTION_FAILED)
            raise ProxyError(f"Couldn't connect to host {remote_host}:{remote_port}") from e
        else:
            await self.respond(ReplyCode.REQUEST_GRANTED)
            return remote

    async def negotiate(self) -> Tuple[str, int]:
        version, command = await self.stream.receive_exactly(2)

        if version != SOCKS_VER4:
            await self.respond(ReplyCode.REQUEST_REJECTED_OR_FAILED)
            raise ProxyError("Invalid socks version")

        if command != Command.CONNECT:
            await self.respond(ReplyCode.REQUEST_REJECTED_OR_FAILED)
            raise ProxyError("Unsupported command")

        port = int.from_bytes(await self.stream.receive_exactly(2), "big")
        host_bytes = await self.stream.receive_exactly(4)

        include_hostname = host_bytes[:3] == bytes([NULL, NULL, NULL])

        user = (await self.read_until_null()).decode("ascii")
        if self.username and self.username != user:
            await self.respond(ReplyCode.AUTHENTICATION_FAILED)
            raise ProxyError("Authentication failed")

        if include_hostname:
            host = (await self.read_until_null()).decode("ascii")
        else:
            host = str(ipaddress.IPv4Address(host_bytes))

        return host, port

    async def read_until_null(self) -> bytes:
        data = bytearray()
        while True:
            byte = ord(await self.stream.receive_exactly(1))
            if byte == NULL:
                break
            data.append(byte)
        return data

    async def respond(self, code: ReplyCode):
        await self.stream.send(
            bytes(
                [
                    RSV,
                    code,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                ]
            )
        )
