from .._stream import SocketStream


class AbstractProxy:
    async def connect_to_remote(self) -> SocketStream:
        raise NotImplementedError()
