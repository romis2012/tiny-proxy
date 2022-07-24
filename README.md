## tiny-proxy

Simple proxy (SOCKS4(a), SOCKS5(h), HTTP tunnel) server built with [anyio](https://github.com/agronholm/anyio).
It is used for testing [python-socks](https://github.com/romis2012/python-socks), [aiohttp-socks](https://github.com/romis2012/aiohttp-socks) and [httpx-socks](https://github.com/romis2012/httpx-socks) packages.

## Requirements
- Python >= 3.7
- anyio>=3.6.1

## Usage

```python
import anyio

from tiny_proxy import Socks5ProxyHandler


async def main():
    handler = Socks5ProxyHandler(username='user', password='password')
    listener = await anyio.create_tcp_listener(local_host='127.0.0.1', local_port=1080)
    await listener.serve(handler.handle)


if __name__ == '__main__':
    anyio.run(main)
```

