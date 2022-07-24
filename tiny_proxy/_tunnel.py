import anyio

from ._stream import SocketStream, DEFAULT_RECEIVE_SIZE


async def create_tunnel(endpoint1: SocketStream, endpoint2: SocketStream):
    async def pipe(reader: SocketStream, writer: SocketStream):
        try:
            while True:
                try:
                    data = await reader.receive(DEFAULT_RECEIVE_SIZE)
                except (
                    anyio.EndOfStream,
                    anyio.ClosedResourceError,
                    anyio.BrokenResourceError,
                ):
                    break

                try:
                    await writer.send(data)
                except (anyio.ClosedResourceError, anyio.BrokenResourceError):
                    break
        finally:
            await writer.aclose()

    async with anyio.create_task_group() as tg:
        tg.start_soon(pipe, endpoint1, endpoint2)
        tg.start_soon(pipe, endpoint2, endpoint1)
