import base64
import binascii
import logging
from collections import namedtuple
from http.server import BaseHTTPRequestHandler
from io import BytesIO
from typing import Tuple

import anyio
import anyio.abc

from .abc import AbstractProxy
from .._errors import ProxyError
from .._stream import SocketStream


class HTTPRequest(BaseHTTPRequestHandler):
    """
    https://stackoverflow.com/questions/4685217/parse-raw-http-headers
    """

    # noinspection PyMissingConstructor
    def __init__(self, data: bytes):
        self.rfile = BytesIO(data)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message=None, explain=None):
        self.error_code = code


class HTTPResponse:
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message


class BasicAuth(namedtuple('BasicAuth', ['login', 'password', 'encoding'])):
    """Http basic authentication helper."""

    def __new__(cls, login: str, password: str = '', encoding: str = 'latin1') -> 'BasicAuth':
        if login is None:
            raise ValueError('None is not allowed as login value')

        if password is None:
            raise ValueError('None is not allowed as password value')

        if ':' in login:
            raise ValueError('A ":" is not allowed in login (RFC 1945#section-11.1)')

        # noinspection PyTypeChecker,PyArgumentList
        return super().__new__(cls, login, password, encoding)

    @classmethod
    def decode(cls, auth_header: str, encoding: str = 'latin1') -> 'BasicAuth':
        """Create a BasicAuth object from an Authorization HTTP header."""
        try:
            auth_type, encoded_credentials = auth_header.split(' ', 1)
        except ValueError:
            raise ValueError('Could not parse authorization header.')

        if auth_type.lower() != 'basic':
            raise ValueError('Unknown authorization method %s' % auth_type)

        try:
            decoded = base64.b64decode(encoded_credentials.encode('ascii'), validate=True).decode(
                encoding
            )
        except binascii.Error:
            raise ValueError('Invalid base64 encoding.')

        try:
            # RFC 2617 HTTP Authentication
            # https://www.ietf.org/rfc/rfc2617.txt
            # the colon must be present, but the username and password may be
            # otherwise blank.
            username, password = decoded.split(':', 1)
        except ValueError:
            raise ValueError('Invalid credentials.')

        # noinspection PyTypeChecker
        return cls(username, password, encoding=encoding)

    def encode(self) -> str:
        """Encode credentials."""
        creds = ('%s:%s' % (self.login, self.password)).encode(self.encoding)
        return 'Basic %s' % base64.b64encode(creds).decode(self.encoding)


class HttpProxy(AbstractProxy):
    def __init__(
        self,
        stream: SocketStream,
        username: str = None,
        password: str = None,
    ):
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
            stream = await anyio.connect_tcp(remote_host=remote_host, remote_port=remote_port)
            remote = SocketStream(stream)
        except OSError as e:
            self.logger.error(e)
            await self.respond(502, 'Bad Gateway', raise_exc=False)
            raise ProxyError(f"Couldn't connect to host {remote_host}:{remote_port}") from e
        else:
            await self.respond(200, 'Connection established')
            return remote

    async def negotiate(self) -> Tuple[str, int]:
        data = await self.stream.receive_until(b'\r\n\r\n', 4096)
        req = HTTPRequest(data)

        if req.error_code:
            await self.respond(int(req.error_code), req.error_message)

        if req.command is None or req.command.lower() != 'connect':
            self.logger.debug(repr(data))
            await self.respond(400, 'Bad Request')

        if self.username and self.password:
            auth_header = req.headers['proxy-authorization']

            if not auth_header:
                await self.respond(401, 'Unauthorized')

            try:
                auth = BasicAuth.decode(auth_header)
            except ValueError:
                await self.respond(401, 'Unauthorized')
            else:
                if auth.login != self.username or auth.password != self.password:
                    await self.respond(401, 'Unauthorized')

        try:
            host, port = req.path.split(":")
            port = int(port)
        except ValueError:
            await self.respond(400, 'Bad Request')
            raise

        return host, port

    async def respond(self, code: int, message: str, raise_exc=True):
        res = f'HTTP/1.1 {code} {message}\r\n\r\n'
        await self.stream.send(res.encode('ascii'))
        if code != 200 and raise_exc:
            raise ProxyError(f'{code} {message}')
