import ssl

from aiohttp import web


async def index(_):
    return web.Response(body='Index')


app = web.Application()
app.router.add_get('/', index)


def run_app(
    host: str,
    port: int,
    ssl_certfile: str = None,
    ssl_keyfile: str = None,
):
    if ssl_certfile and ssl_keyfile:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(ssl_certfile, ssl_keyfile)
    else:
        ssl_context = None

    web.run_app(
        app,
        host=host,
        port=port,
        ssl_context=ssl_context,
        print=False,  #  type: ignore
    )
