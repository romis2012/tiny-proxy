import anyio
import anyio.abc
from anyio.streams.buffered import BufferedByteReceiveStream

DEFAULT_RECEIVE_SIZE = 65536


class SocketStream:
    def __init__(self, stream: anyio.abc.SocketStream):
        self._stream = stream
        self._buffered = BufferedByteReceiveStream(stream)
        self._closing = False

    async def send(self, data: bytes) -> None:
        await self._stream.send(data)

    async def send_eof(self) -> None:
        await self._stream.send_eof()

    async def receive(self, max_bytes=DEFAULT_RECEIVE_SIZE) -> bytes:
        return await self._buffered.receive(max_bytes)

    async def receive_exactly(self, n) -> bytes:
        return await self._buffered.receive_exactly(n)

    async def receive_until(self, delimiter: bytes, max_bytes: int) -> bytes:
        return await self._buffered.receive_until(delimiter, max_bytes)

    async def aclose(self):
        if not self._closing:
            self._closing = True
            await self._buffered.aclose()

    def getpeername(self):
        return self._stream.extra(anyio.abc.SocketAttribute.remote_address, '')

    def getsockname(self):
        return self._stream.extra(anyio.abc.SocketAttribute.local_address, '')
