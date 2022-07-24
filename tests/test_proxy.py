"""
python -m pytest tests --cov=./tiny_proxy --cov-report term-missing -s
"""
import ssl

import httpx
import pytest
from httpx import Response
from httpx_socks import AsyncProxyTransport

from tests.config import (
    SOCKS5_PROXY_URL,
    TEST_HTTPS_URL_IPV4,
    TEST_HTTPS_URL_IPV6,
    TEST_HTTP_URL_IPV4,
    SOCKS5_PROXY_URL_NO_AUTH,
    SOCKS4_PROXY_URL,
    SOCKS4_PROXY_URL_NO_AUTH,
    HTTP_PROXY_URL,
    HTTP_PROXY_URL_NO_AUTH,
)


async def fetch(
    proxy_url: str,
    target_url: str,
    proxy_ssl: ssl.SSLContext = None,
    target_ssl: ssl.SSLContext = None,
    timeout: httpx.Timeout = None,
    **kwargs,
) -> Response:

    transport = AsyncProxyTransport.from_url(
        proxy_url,
        proxy_ssl=proxy_ssl,
        verify=target_ssl,
        **kwargs,
    )
    async with httpx.AsyncClient(transport=transport) as client:
        res = await client.get(target_url, timeout=timeout)
        return res


@pytest.mark.parametrize('url', (TEST_HTTP_URL_IPV4,))
@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks5_proxy_http(url, rdns):
    res = await fetch(
        proxy_url=SOCKS5_PROXY_URL,
        target_url=url,
        rdns=rdns,
    )
    assert res.status_code == 200


@pytest.mark.parametrize('url', (TEST_HTTPS_URL_IPV4, TEST_HTTPS_URL_IPV6))
@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks5_proxy_https(client_ssl_context, url, rdns):
    res = await fetch(
        proxy_url=SOCKS5_PROXY_URL,
        target_url=url,
        target_ssl=client_ssl_context,
        rdns=rdns,
    )
    assert res.status_code == 200


@pytest.mark.parametrize('url', (TEST_HTTPS_URL_IPV4, TEST_HTTPS_URL_IPV6))
@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks5_proxy_https_no_auth(client_ssl_context, url, rdns):
    res = await fetch(
        proxy_url=SOCKS5_PROXY_URL_NO_AUTH,
        target_url=url,
        target_ssl=client_ssl_context,
        rdns=rdns,
    )
    assert res.status_code == 200


@pytest.mark.parametrize('url', (TEST_HTTPS_URL_IPV4,))
@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks4_proxy_https(client_ssl_context, url, rdns):
    res = await fetch(
        proxy_url=SOCKS4_PROXY_URL,
        target_url=url,
        target_ssl=client_ssl_context,
        rdns=rdns,
    )
    assert res.status_code == 200


@pytest.mark.parametrize('url', (TEST_HTTPS_URL_IPV4,))
@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks4_proxy_https_no_auth(client_ssl_context, url, rdns):
    res = await fetch(
        proxy_url=SOCKS4_PROXY_URL_NO_AUTH,
        target_url=url,
        target_ssl=client_ssl_context,
        rdns=rdns,
    )
    assert res.status_code == 200


@pytest.mark.parametrize('url', (TEST_HTTPS_URL_IPV4,))
@pytest.mark.asyncio
async def test_http_proxy_https(client_ssl_context, url):
    res = await fetch(
        proxy_url=HTTP_PROXY_URL,
        target_url=url,
        target_ssl=client_ssl_context,
    )
    assert res.status_code == 200


@pytest.mark.parametrize('url', (TEST_HTTPS_URL_IPV4,))
@pytest.mark.asyncio
async def test_http_proxy_https_no_auth(client_ssl_context, url):
    res = await fetch(
        proxy_url=HTTP_PROXY_URL_NO_AUTH,
        target_url=url,
        target_ssl=client_ssl_context,
    )
    assert res.status_code == 200
