TEST_HTTP_HOST_IPV4 = '127.0.0.1'
TEST_HTTP_PORT_IPV4 = 8881
TEST_HTTP_URL_IPV4 = f'http://{TEST_HTTP_HOST_IPV4}:{TEST_HTTP_PORT_IPV4}/'

TEST_HTTPS_HOST_IPV4 = '127.0.0.1'
TEST_HTTPS_PORT_IPV4 = 8882
TEST_HTTPS_URL_IPV4 = f'https://{TEST_HTTPS_HOST_IPV4}:{TEST_HTTPS_PORT_IPV4}/'

TEST_HTTPS_HOST_IPV6 = '::1'
TEST_HTTPS_PORT_IPV6 = 8883
TEST_HTTPS_URL_IPV6 = f'https://[{TEST_HTTPS_HOST_IPV6}]:{TEST_HTTPS_PORT_IPV6}/'

PROXY_USERNAME = 'username'
PROXY_PASSWORD = 'password'

PROXY_HOST = '127.0.0.1'

SOCKS5_PROXY_PORT = 7780
SOCKS5_PROXY_PORT_NO_AUTH = 7781

SOCKS4_PROXY_PORT = 7782
SOCKS4_PROXY_PORT_NO_AUTH = 7783

HTTP_PROXY_PORT = 7784
HTTP_PROXY_PORT_NO_AUTH = 7785

SOCKS5_PROXY_URL = 'socks5://{username}:{password}@{host}:{port}'.format(
    host=PROXY_HOST,
    port=SOCKS5_PROXY_PORT,
    username=PROXY_USERNAME,
    password=PROXY_PASSWORD,
)

SOCKS5_PROXY_URL_NO_AUTH = 'socks5://{host}:{port}'.format(
    host=PROXY_HOST,
    port=SOCKS5_PROXY_PORT_NO_AUTH,
)

SOCKS4_PROXY_URL = 'socks4://{username}:{password}@{host}:{port}'.format(
    host=PROXY_HOST,
    port=SOCKS4_PROXY_PORT,
    username=PROXY_USERNAME,
    password='',
)

SOCKS4_PROXY_URL_NO_AUTH = 'socks4://{host}:{port}'.format(
    host=PROXY_HOST,
    port=SOCKS4_PROXY_PORT_NO_AUTH,
)

HTTP_PROXY_URL = 'http://{username}:{password}@{host}:{port}'.format(
    host=PROXY_HOST,
    port=HTTP_PROXY_PORT,
    username=PROXY_USERNAME,
    password=PROXY_PASSWORD,
)

HTTP_PROXY_URL_NO_AUTH = 'http://{host}:{port}'.format(
    host=PROXY_HOST,
    port=HTTP_PROXY_PORT_NO_AUTH,
)
