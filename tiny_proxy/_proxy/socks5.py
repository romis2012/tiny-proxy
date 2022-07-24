import enum
import ipaddress
import logging

import anyio
import anyio.abc

from .._stream import SocketStream
from .._errors import ProxyError
from .abc import AbstractProxy

RSV = NULL = 0x00
SOCKS_VER5 = 0x05

SOCKS5_GRANTED = 0x00


class AuthMethod(enum.IntEnum):
    ANONYMOUS = 0x00
    GSSAPI = 0x01
    USERNAME_PASSWORD = 0x02
    NO_ACCEPTABLE = 0xFF


class AddressType(enum.IntEnum):
    IPV4 = 0x01
    DOMAIN = 0x03
    IPV6 = 0x04

    @classmethod
    def from_ip_ver(cls, ver: int):
        if ver == 4:
            return cls.IPV4
        if ver == 6:
            return cls.IPV6

        raise ValueError('Invalid IP version')


class Command(enum.IntEnum):
    CONNECT = 0x01
    BIND = 0x02
    UDP_ASSOCIATE = 0x03


class ReplyCode(enum.IntEnum):
    SUCCEEDED = 0x00
    GENERAL_FAILURE = 0x01
    CONNECTION_NOT_ALLOWED = 0x02
    NETWORK_UNREACHABLE = 0x03
    HOST_UNREACHABLE = 0x04
    CONNECTION_REFUSED = 0x05
    TTL_EXPIRED = 0x06
    COMMAND_NOT_SUPPORTED = 0x07
    ADDRESS_TYPE_NOT_SUPPORTED = 0x08


ReplyMessages = {
    ReplyCode.SUCCEEDED: 'Request granted',
    ReplyCode.GENERAL_FAILURE: 'General SOCKS server failure',
    ReplyCode.CONNECTION_NOT_ALLOWED: 'Connection not allowed by ruleset',
    ReplyCode.NETWORK_UNREACHABLE: 'Network unreachable',
    ReplyCode.HOST_UNREACHABLE: 'Host unreachable',
    ReplyCode.CONNECTION_REFUSED: 'Connection refused by destination host',
    ReplyCode.TTL_EXPIRED: 'TTL expired',
    ReplyCode.COMMAND_NOT_SUPPORTED: 'Command not supported or protocol error',
    ReplyCode.ADDRESS_TYPE_NOT_SUPPORTED: 'Address type not supported',
}


class Socks5Proxy(AbstractProxy):
    def __init__(self, stream: SocketStream, username=None, password=None):
        self.stream = stream
        self.username = username
        self.password = password
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
            # todo: add timeout?
            stream = await anyio.connect_tcp(remote_host=remote_host, remote_port=remote_port)
            remote = SocketStream(stream)
        except OSError as e:
            reply = bytes([SOCKS_VER5, ReplyCode.CONNECTION_REFUSED, NULL, NULL, NULL, NULL])
            await self.stream.send(reply)
            raise ProxyError(f"Couldn't connect to host {remote_host}:{remote_port}") from e
        else:
            bind_address = remote.getsockname()
            bind_ip = ipaddress.ip_address(bind_address[0])
            bind_port = bind_address[1]

            reply = bytearray(
                [
                    SOCKS_VER5,
                    ReplyCode.SUCCEEDED,
                    RSV,
                    AddressType.from_ip_ver(bind_ip.version),
                ]
            )
            reply += bind_ip.packed
            reply += bind_port.to_bytes(2, 'big')

            await self.stream.send(reply)

            return remote

    async def negotiate(self):
        auth_required = self.username and self.password

        # ------------------------AUTH METHODS---------------------
        version, num_methods = await self.stream.receive_exactly(2)

        if version != SOCKS_VER5:
            await self.stream.send(bytes([NULL, NULL]))
            raise ProxyError('Unsupported socks version')

        methods = []
        for i in range(num_methods):
            methods.append(ord(await self.stream.receive_exactly(1)))

        if auth_required:
            auth_method = (
                AuthMethod.USERNAME_PASSWORD
                if AuthMethod.USERNAME_PASSWORD in methods
                else AuthMethod.NO_ACCEPTABLE
            )
        else:
            auth_method = (
                AuthMethod.ANONYMOUS
                if AuthMethod.ANONYMOUS in methods
                else AuthMethod.NO_ACCEPTABLE
            )

        await self.stream.send(bytes([SOCKS_VER5, auth_method]))
        if auth_method == AuthMethod.NO_ACCEPTABLE:
            raise ProxyError('Not acceptable auth method')

        # -----------------------AUTH REQUEST-----------------------
        if auth_method == AuthMethod.USERNAME_PASSWORD:
            version = ord(await self.stream.receive_exactly(1))
            if version != 1:
                await self.stream.send(bytes([version, 0xFF]))
                raise ProxyError('Invalid auth request')

            username_len = ord(await self.stream.receive_exactly(1))
            username = (await self.stream.receive_exactly(username_len)).decode('utf-8')

            password_len = ord(await self.stream.receive_exactly(1))
            password = (await self.stream.receive_exactly(password_len)).decode('utf-8')

            if username == self.username and password == self.password:
                await self.stream.send(bytes([version, SOCKS5_GRANTED]))
            else:
                await self.stream.send(bytes([version, 0xFF]))
                raise ProxyError('Authentication failed')

        # --------------------------CONNECT-----------------------------
        version, cmd, _, address_type = await self.stream.receive_exactly(4)

        if version != SOCKS_VER5:
            await self.stream.send(bytes([SOCKS_VER5, ReplyCode.GENERAL_FAILURE, RSV]))
            raise ProxyError(ReplyMessages[ReplyCode.GENERAL_FAILURE])

        if cmd != Command.CONNECT:
            await self.stream.send(bytes([SOCKS_VER5, ReplyCode.COMMAND_NOT_SUPPORTED, RSV]))
            raise ProxyError(ReplyMessages[ReplyCode.COMMAND_NOT_SUPPORTED])

        if address_type == AddressType.IPV4:
            remote_host = str(ipaddress.IPv4Address(await self.stream.receive_exactly(4)))
        elif address_type == AddressType.IPV6:
            remote_host = str(ipaddress.IPv6Address(await self.stream.receive_exactly(16)))
        elif address_type == AddressType.DOMAIN:
            domain_length = ord(await self.stream.receive_exactly(1))
            remote_host = (await self.stream.receive_exactly(domain_length)).decode('ascii')
        else:
            await self.stream.send(
                bytes([SOCKS_VER5, ReplyCode.ADDRESS_TYPE_NOT_SUPPORTED, NULL, NULL, NULL, NULL])
            )
            raise ProxyError(ReplyMessages[ReplyCode.ADDRESS_TYPE_NOT_SUPPORTED])

        remote_port = int.from_bytes(await self.stream.receive_exactly(2), 'big')

        return remote_host, remote_port
