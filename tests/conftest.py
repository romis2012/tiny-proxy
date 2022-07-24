import ssl

import pytest
import trustme

from tests.config import (
    TEST_HTTP_HOST_IPV4,
    TEST_HTTP_PORT_IPV4,
    PROXY_HOST,
    SOCKS5_PROXY_PORT,
    PROXY_USERNAME,
    PROXY_PASSWORD,
    SOCKS5_PROXY_PORT_NO_AUTH,
    SOCKS4_PROXY_PORT,
    SOCKS4_PROXY_PORT_NO_AUTH,
    HTTP_PROXY_PORT,
    HTTP_PROXY_PORT_NO_AUTH,
    TEST_HTTPS_HOST_IPV4,
    TEST_HTTPS_PORT_IPV4,
    TEST_HTTPS_HOST_IPV6,
    TEST_HTTPS_PORT_IPV6,
)
from tests.http_server import HttpServerConfig, HttpServer
from tests.proxy_server import ProxyConfig, ProxyServerRunner
from tests.utils import wait_until_connectable


@pytest.fixture(scope='session')
def ssl_ca() -> trustme.CA:
    return trustme.CA()


@pytest.fixture(scope='session')
def ssl_cert(ssl_ca: trustme.CA) -> trustme.LeafCert:
    return ssl_ca.issue_cert(
        "localhost",
        "127.0.0.1",
        "::1",
    )


@pytest.fixture(scope='session')
def ssl_certfile(ssl_cert: trustme.LeafCert):
    with ssl_cert.cert_chain_pems[0].tempfile() as cert_path:
        yield cert_path


@pytest.fixture(scope='session')
def ssl_keyfile(ssl_cert: trustme.LeafCert):
    with ssl_cert.private_key_pem.tempfile() as private_key_path:
        yield private_key_path


@pytest.fixture(scope='session')
def ssl_key_and_cert_chain_file(ssl_cert: trustme.LeafCert):
    with ssl_cert.private_key_and_cert_chain_pem.tempfile() as path:
        yield path


@pytest.fixture(scope='session')
def ssl_ca_cert_file(ssl_ca: trustme.CA):
    with ssl_ca.cert_pem.tempfile() as ca_cert_pem:
        yield ca_cert_pem


@pytest.fixture(scope='session')
def server_ssl_context(ssl_cert: trustme.LeafCert) -> ssl.SSLContext:
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_cert.configure_cert(ssl_ctx)
    return ssl_ctx


@pytest.fixture(scope='session')
def client_ssl_context(ssl_ca: trustme.CA, ssl_ca_cert_file) -> ssl.SSLContext:
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_ctx.verify_mode = ssl.CERT_REQUIRED
    ssl_ctx.check_hostname = True

    # ssl_ctx.load_verify_locations(ssl_ca_cert_file)
    ssl_ca.configure_trust(ssl_ctx)

    return ssl_ctx


@pytest.fixture(scope='session', autouse=True)
def web_server(ssl_certfile, ssl_keyfile):
    config = [
        HttpServerConfig(
            host=TEST_HTTP_HOST_IPV4,
            port=TEST_HTTP_PORT_IPV4,
        ),
        HttpServerConfig(
            host=TEST_HTTPS_HOST_IPV4,
            port=TEST_HTTPS_PORT_IPV4,
            ssl_certfile=ssl_certfile,
            ssl_keyfile=ssl_keyfile,
        ),
        HttpServerConfig(
            host=TEST_HTTPS_HOST_IPV6,
            port=TEST_HTTPS_PORT_IPV6,
            ssl_certfile=ssl_certfile,
            ssl_keyfile=ssl_keyfile,
        ),
    ]

    server = HttpServer(config=config)
    server.run()

    for cfg in config:
        wait_until_connectable(host=cfg.host, port=cfg.port)

    yield None

    server.shutdown()


@pytest.fixture(scope='session', autouse=True)
def proxy_server():
    config = [
        ProxyConfig(
            proxy_type='socks5',
            host=PROXY_HOST,
            port=SOCKS5_PROXY_PORT,
            username=PROXY_USERNAME,
            password=PROXY_PASSWORD,
        ),
        ProxyConfig(
            proxy_type='socks5',
            host=PROXY_HOST,
            port=SOCKS5_PROXY_PORT_NO_AUTH,
        ),
        ProxyConfig(
            proxy_type='socks4',
            host=PROXY_HOST,
            port=SOCKS4_PROXY_PORT,
            username=PROXY_USERNAME,
            password=None,
        ),
        ProxyConfig(
            proxy_type='socks4',
            host=PROXY_HOST,
            port=SOCKS4_PROXY_PORT_NO_AUTH,
        ),
        ProxyConfig(
            proxy_type='http',
            host=PROXY_HOST,
            port=HTTP_PROXY_PORT,
            username=PROXY_USERNAME,
            password=PROXY_PASSWORD,
        ),
        ProxyConfig(
            proxy_type='http',
            host=PROXY_HOST,
            port=HTTP_PROXY_PORT_NO_AUTH,
        ),
    ]

    server = ProxyServerRunner(config=config)
    server.run()
    for cfg in config:
        wait_until_connectable(host=cfg.host, port=cfg.port)

    yield None

    server.shutdown()
